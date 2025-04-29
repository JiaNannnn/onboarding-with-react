"""
BMS Routes Module

This module defines the Flask routes for BMS-related API endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from ..services.bms_service import BMSService
from flasgger import swag_from

# Create Blueprint
bms_bp = Blueprint('bms', __name__, url_prefix='/api/bms')

# Create service instance
bms_service = BMSService()

@bms_bp.route('/networks', methods=['GET'])
@swag_from({
    'tags': ['BMS'],
    'summary': 'Get available BMS networks',
    'description': 'Retrieves network configuration for BACnet networks',
    'parameters': [
        {
            'name': 'asset_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Asset ID (defaults to configured default)'
        }
    ],
    'responses': {
        '200': {
            'description': 'List of available networks',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'},
                    'data': {'type': 'array'}
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        }
    }
})
def get_networks():
    """
    Get available BMS networks.
    """
    try:
        # Get asset_id from query parameters or use default
        asset_id = request.args.get('asset_id')
        
        current_app.logger.info(f"Getting networks for asset ID: {asset_id or 'default'}")
        result = bms_service.get_network_config(asset_id)
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_networks: {str(e)}")
        return jsonify({"code": 1, "msg": str(e)}), 500

@bms_bp.route('/devices', methods=['POST'])
@swag_from({
    'tags': ['BMS'],
    'summary': 'Discover BMS devices',
    'description': 'Initiates a BACnet scan to discover devices on a specific network',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'asset_id': {'type': 'string', 'description': 'Asset ID'},
                    'network': {'type': 'string', 'description': 'Network to scan'}
                },
                'required': ['network']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Device discovery results',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'result': {
                        'type': 'object',
                        'properties': {
                            'deviceList': {'type': 'array'},
                            'deviceCount': {'type': 'integer'},
                            'resultFile': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '400': {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        }
    }
})
def discover_devices():
    """
    Discover BMS devices on a specific network.
    """
    try:
        # Get request JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({"code": 1, "msg": "No data provided"}), 400
        
        # Extract parameters
        asset_id = data.get('asset_id')
        network = data.get('network')
        
        if not network:
            return jsonify({"code": 1, "msg": "Network is required"}), 400
        
        current_app.logger.info(f"Discovering devices on network {network} for asset ID: {asset_id or 'default'}")
        result = bms_service.discover_devices(asset_id, network)
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error in discover_devices: {str(e)}")
        return jsonify({"code": 1, "msg": str(e)}), 500

@bms_bp.route('/devices/<asset_id>', methods=['GET'])
@swag_from({
    'tags': ['BMS'],
    'summary': 'Get discovered BMS devices',
    'description': 'Retrieves the list of discovered BACnet devices for an asset',
    'parameters': [
        {
            'name': 'asset_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Asset ID'
        }
    ],
    'responses': {
        '200': {
            'description': 'List of discovered devices',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'result': {
                        'type': 'object',
                        'properties': {
                            'deviceList': {'type': 'array'},
                            'deviceCount': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        }
    }
})
def get_devices(asset_id):
    """
    Get discovered BMS devices for an asset.
    """
    try:
        current_app.logger.info(f"Getting devices for asset ID: {asset_id}")
        result = bms_service.fetch_devices(asset_id)
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_devices: {str(e)}")
        return jsonify({"code": 1, "msg": str(e)}), 500

@bms_bp.route('/points', methods=['POST'])
@swag_from({
    'tags': ['BMS'],
    'summary': 'Fetch BMS points for devices',
    'description': 'Retrieves BACnet points for one or more devices',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'asset_id': {'type': 'string', 'description': 'Asset ID'},
                    'devices': {
                        'type': 'array',
                        'description': 'Devices to fetch points for',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'otDeviceInst': {'type': 'string', 'description': 'Device instance number'},
                                'address': {'type': 'string', 'description': 'Device IP address'},
                                'deviceName': {'type': 'string', 'description': 'Device name'}
                            },
                            'required': ['otDeviceInst']
                        }
                    }
                },
                'required': ['asset_id', 'devices']
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Points for requested devices',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'},
                    'point_results': {'type': 'object'},
                    'all_points': {'type': 'array'},
                    'device_count': {'type': 'integer'},
                    'total_points': {'type': 'integer'}
                }
            }
        },
        '400': {
            'description': 'Bad request',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        }
    }
})
def get_points():
    """
    Fetch BMS points for devices.
    """
    try:
        # Get request JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({"code": 1, "msg": "No data provided"}), 400
        
        # Extract parameters
        asset_id = data.get('asset_id')
        devices = data.get('devices', [])
        
        if not asset_id:
            return jsonify({"code": 1, "msg": "Asset ID is required"}), 400
        
        if not devices:
            return jsonify({"code": 1, "msg": "At least one device is required"}), 400
        
        current_app.logger.info(f"Fetching points for {len(devices)} devices on asset ID: {asset_id}")
        result = bms_service.fetch_points_for_devices(asset_id, devices)
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_points: {str(e)}")
        return jsonify({"code": 1, "msg": str(e)}), 500

@bms_bp.route('/points/<asset_id>/<device_instance>', methods=['GET'])
@swag_from({
    'tags': ['BMS'],
    'summary': 'Fetch BMS points for a specific device',
    'description': 'Retrieves BACnet points for a specific device by instance number',
    'parameters': [
        {
            'name': 'asset_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Asset ID'
        },
        {
            'name': 'device_instance',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Device instance number'
        },
        {
            'name': 'device_address',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Device IP address'
        }
    ],
    'responses': {
        '200': {
            'description': 'Points for the requested device',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'},
                    'result': {
                        'type': 'object',
                        'properties': {
                            'objectPropertys': {'type': 'array'},
                            'count': {'type': 'integer'},
                            'resultFile': {'type': 'string'}
                        }
                    }
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'msg': {'type': 'string'}
                }
            }
        }
    }
})
def get_device_points(asset_id, device_instance):
    """
    Fetch BMS points for a specific device.
    """
    try:
        # Get device address from query parameters
        device_address = request.args.get('device_address', 'unknown-ip')
        
        current_app.logger.info(f"Fetching points for device {device_instance} on asset ID: {asset_id}")
        result = bms_service.fetch_points(asset_id, device_instance, device_address)
        
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_device_points: {str(e)}")
        return jsonify({"code": 1, "msg": str(e)}), 500 