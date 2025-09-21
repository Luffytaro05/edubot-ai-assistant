from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

faq_bp = Blueprint('faq_bp', __name__)

# Initialize MongoDB client
client = MongoClient('mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/')
db = client['chatbot_db']
faqs_col = db['faqs']
offices_col = db['offices']

# ----------------------
# Office Endpoints
# ----------------------
@faq_bp.route('/api/offices', methods=['GET'])
def get_offices():
    offices = list(offices_col.find())
    for o in offices:
        o['_id'] = str(o['_id'])
    return jsonify(success=True, offices=offices)

@faq_bp.route('/api/offices', methods=['POST'])
def add_office():
    data = request.json
    name = data.get('name')
    description = data.get('description')
    icon = data.get('icon')  # NEW: get icon from request
    if not name or not icon:
        return jsonify(success=False, message='Office name and icon are required'), 400

    office_id = offices_col.insert_one({
        'name': name,
        'description': description,
        'icon': icon,  # save icon in MongoDB
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }).inserted_id

    office = offices_col.find_one({'_id': office_id})
    office['_id'] = str(office['_id'])
    return jsonify(success=True, office=office)


# ----------------------
# FAQ Endpoints
# ----------------------
@faq_bp.route('/api/faqs', methods=['GET'])
def get_faqs():
    faqs = list(faqs_col.find())
    for f in faqs:
        f['_id'] = str(f['_id'])
    return jsonify(success=True, faqs=faqs)

@faq_bp.route('/api/faqs', methods=['POST'])
def add_faq():
    data = request.json
    office = data.get('office')
    question = data.get('question')
    answer = data.get('answer')
    status = data.get('status', 'draft')

    if not office or not question or not answer:
        return jsonify(success=False, message='All fields are required'), 400

    if not offices_col.find_one({'name': office}):
        return jsonify(success=False, message='Invalid office'), 400

    faq_id = faqs_col.insert_one({
        'office': office,
        'question': question,
        'answer': answer,
        'status': status,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }).inserted_id

    faq = faqs_col.find_one({'_id': faq_id})
    faq['_id'] = str(faq['_id'])
    return jsonify(success=True, faq=faq)

@faq_bp.route('/api/faqs/<faq_id>', methods=['PUT'])
def update_faq(faq_id):
    data = request.json
    office = data.get('office')
    question = data.get('question')
    answer = data.get('answer')
    status = data.get('status', 'draft')

    if not office or not question or not answer:
        return jsonify(success=False, message='All fields are required'), 400

    if not offices_col.find_one({'name': office}):
        return jsonify(success=False, message='Invalid office'), 400

    result = faqs_col.update_one(
        {'_id': ObjectId(faq_id)},
        {'$set': {
            'office': office,
            'question': question,
            'answer': answer,
            'status': status,
            'updated_at': datetime.utcnow()
        }}
    )
    if result.matched_count == 0:
        return jsonify(success=False, message='FAQ not found'), 404

    faq = faqs_col.find_one({'_id': ObjectId(faq_id)})
    faq['_id'] = str(faq['_id'])
    return jsonify(success=True, faq=faq)

@faq_bp.route('/api/faqs/<faq_id>', methods=['DELETE'])
def delete_faq(faq_id):
    result = faqs_col.delete_one({'_id': ObjectId(faq_id)})
    if result.deleted_count == 0:
        return jsonify(success=False, message='FAQ not found'), 404
    return jsonify(success=True)
