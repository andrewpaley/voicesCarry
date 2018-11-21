import flask
from flask import request, jsonify
from flask import Blueprint
from jumbodb import JumboDB
from trunk import Trunk

jumbo = Blueprint('jumbo', __name__)

@jumbo.route('/jumbo', methods=['GET'])
def home():
    # TODO if an API becomes necessary
    return ""
