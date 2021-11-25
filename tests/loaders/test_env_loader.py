from typing import Optional
from unittest import mock

import pytest
from confz import ConfZ, ConfZEnvSource
from pydantic import ValidationError


class InnerConfig(ConfZ):
    attr1_name: int
    attr_override: Optional[str]

class OuterConfig(ConfZ):
    attr2: int
    inner: InnerConfig


def test_allow_all(monkeypatch): 
    monkeypatch.setenv('ATTR2', '2')   
    monkeypatch.setenv('INNER.ATTR1-NAME', '1') 
    monkeypatch.setenv('INNER.ATTR-OVERRIDE', 'secret')   
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow_all=True
    ))
    assert config.inner.attr1_name == 1
    assert config.attr2 == 2
    assert config.inner.attr_override == 'secret'

def test_allow_deny(monkeypatch):
    monkeypatch.setenv('ATTR2', '2')    
    monkeypatch.setenv('INNER.ATTR1-NAME', '1') 
    monkeypatch.setenv('INNER.ATTR-OVERRIDE', 'secret')      

    # works if all allowed
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow=['inner.attr1_name', 'attr2']
    ))
    assert config.attr2 == 2    
    assert config.inner.attr1_name == 1
    assert config.inner.attr_override == None
    
    # raises error if not all allowed
    with pytest.raises(ValidationError):
        OuterConfig(config_sources=ConfZEnvSource(
            allow=['attr2']
        ))

    # raises error if denied
    with pytest.raises(ValidationError):
        OuterConfig(config_sources=ConfZEnvSource(
            allow=['inner.attr1_name', 'attr2'],
            deny=['attr2']
        ))


def test_prefix(monkeypatch):
    monkeypatch.setenv('CONFIG_INNER.ATTR1-NAME', '1')
    monkeypatch.setenv('CONFIG_ATTR2', '2')

    # prefix works
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow_all=True,
        prefix='CONFIG_'
    ))
    assert config.attr2 == 2
    assert config.inner.attr1_name == 1

    # allow does not use prefix
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow=['inner.attr1_name', 'attr2'],
        prefix='CONFIG_'
    ))
    assert config.attr2 == 2    
    assert config.inner.attr1_name == 1

    # deny does not use prefix
    with pytest.raises(ValidationError):
        OuterConfig(config_sources=ConfZEnvSource(
            allow_all=True,
            deny=['attr2'],
            prefix='CONFIG_'
        ))


def test_remap(monkeypatch):
    # remap works
    monkeypatch.setenv('VAL1', '1')
    monkeypatch.setenv('VAL2', '2')
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow_all=True,
        remap={
            'val1': 'inner.attr1_name',
            'val2': 'attr2',
        }
    ))
    assert config.attr2 == 2    
    assert config.inner.attr1_name == 1

    # remap does not use prefix
    monkeypatch.setenv('CONFIG_VAL1', '3')
    monkeypatch.setenv('CONFIG_VAL2', '4')
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow_all=True,
        prefix='CONFIG_',
        remap={
            'val1': 'inner.attr1_name',
            'val2': 'attr2',
        }
    ))
    assert config.attr2 == 4    
    assert config.inner.attr1_name == 3
    
    
def test_dotenv_loading(monkeypatch):
    monkeypatch.setattr('os.path.isfile', lambda _: True)
    monkeypatch.setattr('io.open', mock.mock_open(read_data="INNER.ATTR1-NAME=2001\nINNER.ATTR-OVERRIDE=2002\n"))
    monkeypatch.setenv('INNER.ATTR1_NAME', '21')
    monkeypatch.setenv('ATTR2', '1')
    config = OuterConfig(config_sources=ConfZEnvSource(
        allow_all=True
    ))
    assert config.attr2 == 1
    assert config.inner.attr1_name == 21
    assert config.inner.attr_override == '2002'
    
