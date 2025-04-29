from app import db
from sqlalchemy.dialects.postgresql import JSONB

class DeviceGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), index=True)  # AHU/FCU/CHPL等
    raw_points = db.Column(JSONB)  # 原始点位列表
    instances = db.relationship('DeviceInstance', backref='group', lazy='dynamic')

class DeviceInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), index=True)  # AHU-1等
    group_id = db.Column(db.Integer, db.ForeignKey('device_group.id'))
    mappings = db.Column(JSONB)  # {raw_point: enos_path}
    status = db.Column(db.String(20))  # pending/partial/complete

class MappingRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.String(200), index=True)
    enos_path = db.Column(db.String(200))  # AHU/points/AHU_raw_status
    confidence = db.Column(db.Float)
    last_validated = db.Column(db.DateTime) 