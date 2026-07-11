local tables = {}

tables.point = osm2pgsql.define_node_table('osm_point', {
    { column = 'tags', type = 'jsonb' },
    { column = 'geom', type = 'point', projection = 3857, not_null = true },
})

tables.line = osm2pgsql.define_way_table('osm_line', {
    { column = 'tags', type = 'jsonb' },
    { column = 'geom', type = 'linestring', projection = 3857, not_null = true },
})

tables.polygon = osm2pgsql.define_area_table('osm_polygon', {
    { column = 'tags', type = 'jsonb' },
    { column = 'geom', type = 'multipolygon', projection = 3857, not_null = true },
})

tables.relation = osm2pgsql.define_relation_table('osm_relation', {
    { column = 'tags', type = 'jsonb' },
})

function osm2pgsql.process_node(object)
    tables.point:insert{
        tags = object.tags,
        geom = object:as_point()
    }
end

function osm2pgsql.process_way(object)
    if object.is_closed then
        tables.polygon:insert{
            tags = object.tags,
            geom = object:as_multipolygon()
        }
    else
        tables.line:insert{
            tags = object.tags,
            geom = object:as_linestring()
        }
    end
end

function osm2pgsql.process_relation(object)
    if object.tags.type == 'multipolygon'
       or object.tags.type == 'boundary' then
        tables.polygon:insert{
            tags = object.tags,
            geom = object:as_multipolygon()
        }
    end

    tables.relation:insert{
        tags = object.tags
    }
end
