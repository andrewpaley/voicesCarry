import flask
from flask import request, jsonify
from flask import Blueprint
from jumbodb import JumboDB
from trunk import Trunk

jumbo = Blueprint('jumbo', __name__)

@jumbo.route('/jumbo', methods=['GET'])
def home():
    return "<h1>Distant Reading Archive</h1><p>This site is a prototype API for distant reading of science fiction novels.</p>"
