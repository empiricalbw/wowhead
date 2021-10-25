import wowhead


def scrape_slot(slot, qualities):
    items = wowhead.query_items([slot], qualities)
    print('Found %u items.' % len(items))
    for i, item in enumerate(items):
        print('Querying (%u / %u) %u: %s...' % (i, len(items), item.item_id,
                                                item.name))
        item.de_info = wowhead.query_disenchant_info(item.item_id)

    buckets = {}
    for i in items:
        b = buckets.get((i.ilvl, i.quality))
        if b is None:
            buckets[(i.ilvl, i.quality)] = b = {}
        for di in i.de_info:
            k = (di[0], di[1])
            r = b.get(k)
            if r is None:
                r = 0
            b[k] = r + di[2]

    return items, buckets


for slot, name in wowhead.SLOT_NAMES:
    items, buckets = scrape_slot(slot,
                                 [wowhead.QUALITY_GREEN,
                                  wowhead.QUALITY_RARE,
                                  wowhead.QUALITY_EPIC]
                                 )

    with open('results/buckets_%s.txt' % name, 'w') as f:
        for (ilvl, quality) in sorted(buckets.keys()):
            s = 'iLvl %u Quality %u' % (ilvl, quality)
            print(s)
            f.write('%s\n' % s)
            b = buckets[(ilvl, quality)]
            total_des = sum(b.values())
            for k in sorted(b.keys()):
                count = b[k]
                s = '   %4u (%4.1f%%) %s x %u' % (count,
                                                  count * 100 / total_des,
                                                  k[0].name, k[1])
                print(s)
                f.write('%s\n' % s)

    with open('results/buckets_%s.py' % name, 'w') as f:
        f.write('Green_BUCKETS = {}\n')
        f.write('Rare_BUCKETS = {}\n')
        f.write('Epic_BUCKETS = {}\n\n')
        for (ilvl, quality) in sorted(buckets.keys()):
            f.write('%s_BUCKETS[%u] = [\n' % (wowhead.QUALITY_NAMES[quality],
                                              ilvl))
            b = buckets[(ilvl, quality)]
            total_des = sum(b.values())
            for k in sorted(b.keys()):
                count = b[k]
                f.write('    ("%s", %u, %u, %u),\n' % (k[0].name, k[0].item_id,
                                                       k[1], count))

            f.write(']\n')

    with open('results/items_%s.lua' % name, 'w') as f:
        f.write('DE_ITEMS_%s = {\n' % name)
        for i in sorted(items):
            if len(i.de_info) == 0:
                continue
            f.write('    [%u] = {\n' % i.item_id)
            for di in i.de_info:
                f.write('        {"%s", %u, %u, %u},\n' % (di[0].name,
                                                           di[0].item_id,
                                                           di[1],
                                                           di[2]))
            f.write('    },\n')
        f.write('}\n')

    with open('results/items_%s.py' % name, 'w') as f:
        f.write('DE_ITEMS_%s = {\n' % name)
        for i in sorted(items):
            if len(i.de_info) == 0:
                continue
            f.write('    %u : [\n' % i.item_id)
            for di in i.de_info:
                f.write('        ("%s", %u, %u, %u),\n' % (di[0].name,
                                                           di[0].item_id,
                                                           di[1],
                                                           di[2]))
            f.write('    ],\n')
        f.write('}\n')
