from apiflask import Schema
from apiflask.fields import String, Integer, Email, Nested, Float, Raw, List
from apiflask.validators import Length, OneOf, Regexp
from marshmallow import INCLUDE

class Image(Schema):
    img = Raw(required=True)
    names = List(String)

class ImageEx(Image):
    containers = List(String)

class Det(Schema):
    index = Integer(required=True)
    x_left = Float(required=True)
    y_top = Float(required=True)
    x_right = Float(required=True)
    y_bottom = Float(required=True)
    confidence = Float(required=True)
    obj_name = String(required=True)
    children = List(Nested(lambda: Det()))

class Weight(Schema):
    file = String()
    img_size = Integer()
    device = String()
    names = List(String)

class AddWeight(Schema):
    file = String(required=True)
    img_size = Integer(required=True)
    device = String(required=True, validate=Regexp('^(cpu|\\d)$'))

class UpdateWeight(Schema):
    file = String()
    img_size = Integer()
    device = String(validate=Regexp('^(cpu|\\d)$'))