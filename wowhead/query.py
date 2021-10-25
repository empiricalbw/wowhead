import requests
import hjson
from lxml import etree
from io import BytesIO

from .item import Item


QUALITY_GRAY         = 0
QUALITY_WHITE        = 1
QUALITY_GREEN        = 2
QUALITY_RARE         = 3
QUALITY_EPIC         = 4
QUALITY_LEGENDARY    = 5

QUALITY_NAMES = {
    QUALITY_GRAY         : 'Gray',
    QUALITY_WHITE        : 'White',
    QUALITY_GREEN        : 'Green',
    QUALITY_RARE         : 'Rare',
    QUALITY_EPIC         : 'Epic',
    QUALITY_LEGENDARY    : 'Legendary',
}

SLOT_HEAD            = 1
SLOT_NECK            = 2
SLOT_SHOULDER        = 3
SLOT_SHIRT           = 4
SLOT_CHEST           = 5
SLOT_WAIST           = 6
SLOT_LEGS            = 7
SLOT_FEET            = 8
SLOT_WRIST           = 9
SLOT_HANDS           = 10
SLOT_FINGER          = 11
SLOT_TRINKET         = 12
SLOT_ONEHAND         = 13
SLOT_SHIELD          = 14
SLOT_RANGED          = 15
SLOT_BACK            = 16
SLOT_TWOHAND         = 17
SLOT_BAG             = 18
SLOT_TABARD          = 19
SLOT_MAINHAND        = 21
SLOT_OFFHAND         = 22
SLOT_HELD_IN_OFFHAND = 23
SLOT_AMMO            = 24
SLOT_THROWN          = 25
SLOT_RELIC           = 28

SLOT_NAMES = {
    SLOT_HEAD            : 'Head',
    SLOT_NECK            : 'Neck',
    SLOT_SHOULDER        : 'Shoulder',
    SLOT_SHIRT           : 'Shirt',
    SLOT_CHEST           : 'Chest',
    SLOT_WAIST           : 'Waist',
    SLOT_LEGS            : 'Legs',
    SLOT_FEET            : 'Feet',
    SLOT_WRIST           : 'Wrist',
    SLOT_HANDS           : 'Hands',
    SLOT_FINGER          : 'Finger',
    SLOT_TRINKET         : 'Trinket',
    SLOT_ONEHAND         : 'One-Hand',
    SLOT_SHIELD          : 'Shield',
    SLOT_RANGED          : 'Ranged',
    SLOT_BACK            : 'Back',
    SLOT_TWOHAND         : 'Two-Hand',
    SLOT_BAG             : 'Bag',
    SLOT_TABARD          : 'Tabard',
    SLOT_MAINHAND        : 'Main-Hand',
    SLOT_OFFHAND         : 'Off-Hand',
    SLOT_HELD_IN_OFFHAND : 'Held-In-Off-Hand',
    SLOT_AMMO            : 'Ammo',
    SLOT_THROWN          : 'Thrown',
    SLOT_RELIC           : 'Relic',
}


def _parse_listviewitems(s):
    assert s.startswith('var listviewitems = [')
    items = []
    s     = s[20:-1]
    j     = hjson.loads(s)
    return [Item(i['id'], i['name'], i['quality'], i['level'],
                 i['classs'], i['subclass'], i['slot'])
            for i in j]


def _parse_disenchanting_data(s):
    # data: [{"classs":7,"flags2":24580,"id":22450,"level":70,
    #         "name":"Void Crystal","quality":4,"slot":0,"source":[15],
    #         "subclass":12,"count":9,"stack":[1,2],
    #         "pctstack":"{1: 55.5556,2: 44.4444}"
    #        }],
    assert s.startswith('data: [')
    results = []
    s       = s[6:-1]
    j       = hjson.loads(s)
    for d in j:
        item = Item(d['id'], d['name'], d['quality'], d['level'], d['classs'],
                    d['subclass'], d['slot'])

        if 'pctstack' in d:
            d['pctstack'] = hjson.loads(d['pctstack'])
        count = d['count']
        if d['stack'][0] == d['stack'][1]:
            assert 'pctstack' not in d
            results.append((item, d['stack'][0], count))
        else:
            for n, pct in d['pctstack'].items():
                stack_des = round(pct * count / 100)
                results.append((item, int(n), stack_des))

    return results


def _query_items(slots, qualities, min_ilvl, max_ilvl):
    url = 'https://tbc.wowhead.com/items'
    if min_ilvl is not None:
        url += '/min-level:%u' % min_ilvl
    if max_ilvl is not None:
        url += '/max-level:%u' % max_ilvl
    if qualities:
        url += '/quality:%s' % ':'.join('%u' % q for q in qualities)
    if slots:
        url += '/slot:%s' % ':'.join('%u' % s for s in slots)

    print(url)
    r      = requests.get(url)
    parser = etree.HTMLParser()
    tree   = etree.parse(BytesIO(r.content), parser)
    elems  = tree.xpath('//div[@class="main-contents"]'
                        '/script[@type="text/javascript"]')
    assert len(elems) <= 1
    if len(elems) == 1:
        for l in elems[0].text.splitlines():
            if not l.startswith('var listviewitems = ['):
                continue
            return _parse_listviewitems(l)

    return []


def query_items(slots, qualities, min_ilvl=None, max_ilvl=None,
                filter_enchants=True):
    items = []
    if min_ilvl is None:
        min_ilvl = 0
    if max_ilvl is None:
        max_ilvl = 164
    for ilvl in range(0, 165, 10):
        range_min = ilvl
        range_max = ilvl + 9
        if range_max < min_ilvl:
            continue
        if range_min > max_ilvl:
            break

        items += _query_items(slots, qualities, max(range_min, min_ilvl),
                              min(range_max, max_ilvl))

    if filter_enchants:
        items = [i for i in items if i.slot in slots]
    return items


def query_disenchant_info(item_id):
    '''
    Returns a list of tuples of the form:

        [(ItemInfo(), N1, count1),
         (ItemInfo(), N2, count2),
         ...
         ]

    The ItemInfo objects represent a possible disenchant result (i.e. Strange
    Dust).  The N integers represent the stack size of the disenchant result
    (i.e. Strange Dust x3).  The count integers represent the total number of
    times this disenchant result has been observed.
    '''
    r      = requests.get('https://tbc.wowhead.com/item=%u' % item_id)
    parser = etree.HTMLParser()
    tree   = etree.parse(BytesIO(r.content), parser)
    elems  = tree.xpath('//div[@class="main-contents"]'
                        '/script[@type="text/javascript"]')

    for e in elems:
        in_listview      = False
        in_disenchanting = False
        for l in e.text.splitlines():
            l = l.strip()
            if l == 'new Listview({':
                assert not in_listview
                in_listview = True
            elif l.startswith('id: \''):
                if l[5:-2] == 'disenchanting':
                    in_disenchanting = True
            elif l.startswith('data: [') and in_disenchanting:
                return _parse_disenchanting_data(l)
            elif l == '});':
                assert in_listview
                in_listview      = False
                in_disenchanting = False

    return []
