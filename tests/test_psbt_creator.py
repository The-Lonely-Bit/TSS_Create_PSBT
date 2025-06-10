import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_psbt_single_transaction(client):
    """Test creating a single PSBT transaction"""
    test_data = {
        "utxos": [{
            "txid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "vout": 0,
            "value": 10000,
            "scriptPubKey": "0014abcdef1234567890abcdef1234567890abcdef12"
        }],
        "outputs": [{
            "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "amount": 9000
        }],
        "fee": 200
    }
    
    response = client.post('/create_psbt',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'psbt' in data
    assert data['fee'] == 200
    assert data['inputs_used'] == 1
    assert data['change'] > 0

def test_create_psbt_insufficient_funds(client):
    """Test creating a PSBT with insufficient funds"""
    test_data = {
        "utxos": [{
            "txid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "vout": 0,
            "value": 1000,
            "scriptPubKey": "0014abcdef1234567890abcdef1234567890abcdef12"
        }],
        "outputs": [{
            "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "amount": 9000
        }],
        "fee": 200
    }
    
    response = client.post('/create_psbt',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Insufficient funds' in data['error']

def test_create_psbt_missing_required_fields(client):
    """Test creating a PSBT with missing required fields"""
    test_data = {
        "utxos": [],
        "outputs": []
    }
    
    response = client.post('/create_psbt',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'utxos and outputs are required' in data['error']

def test_create_psbt_with_fee_rate(client):
    """Test creating a PSBT with fee rate instead of flat fee"""
    test_data = {
        "utxos": [{
            "txid": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "vout": 0,
            "value": 10000,
            "scriptPubKey": "0014abcdef1234567890abcdef1234567890abcdef12"
        }],
        "outputs": [{
            "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "amount": 9000
        }],
        "fee_rate": 1.5
    }
    
    response = client.post('/create_psbt',
                          data=json.dumps(test_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'psbt' in data
    assert 'fee_rate' in data
    assert 'vsize' in data
    assert data['fee_rate'] == 1.5 