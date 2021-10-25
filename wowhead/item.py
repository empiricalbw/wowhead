import requests
import json
from lxml import etree
from io import BytesIO

class Item:
    def __init__(self, item_id, name, quality, ilvl, classs, subclass, slot):
        self.item_id  = item_id
        self.name     = name
        self.quality  = quality
        self.ilvl     = ilvl
        self.classs   = classs
        self.subclass = subclass
        self.slot     = slot
        self.de_info  = None

    def __repr__(self):
        return 'Item(name="%s")' % self.name

    def __lt__(self, other):
        assert isinstance(other, Item)
        return self.item_id < other.item_id

    def __eq__(self, other):
        return isinstance(other, Item) and other.item_id == self.item_id

    def __hash__(self):
        return self.item_id

    @staticmethod
    def from_item_id(item_id):
        r      = requests.get('https://tbc.wowhead.com/item=%u&xml' % item_id)
        parser = etree.XMLParser()
        tree   = etree.parse(BytesIO(r.content), parser)
        elems  = tree.xpath('/wowhead/item/json')
        assert len(elems) == 1
        e      = elems[0]
        j      = json.loads('{%s}' % e.text)
        return Item(item_id, j['name'], j['quality'], j['level'], j['classs'],
                    j['subclass'], j['slot'])

    @staticmethod
    def key_ilvl(item):
        return item.ilvl

    def load_de_info(self):
        self.de_info = query_disenchant_info(self.item_id)

    def dump(self):
        print(' Item: %s' % self.name)
        print(' iLvl: %u' % self.ilvl)
        print(' Qual: %u' % self.quality)
        print('https://tbc.wowhead.com/item=%u' % self.item_id)
