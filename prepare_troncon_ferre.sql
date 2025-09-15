drop table if exists bdtopo.train_buffer;
create table bdtopo.train_buffer as
select uuid_generate_v4() as id,'train'::text as nature
, ST_Transform(ST_Buffer(ST_UNION(geom), 12.5 , 'endcap=flat join=round'),2154) as geom from bdtopo.troncon_ferree
 where nature in ('Voie ferrée principale','Tramway','LGV','Métro')
 and etat_de_l_objet = 'En service'
 ;
 
 alter table bdtopo.train_buffer add primary key(id);
 
  

update bdtopo.train_buffer set geom = st_makevalid(geom);
update bdtopo.train_buffer set geom = st_simplify(geom,0.5);


drop table if exists bdtopo.trains_buffer;
create table bdtopo.trains_buffer as
select uuid_generate_v4() as id,
CASE when nature = 'Voie ferrée principale' then 'TER/RER' 
     when nature = 'LGV' then 'TGV' 
	 else nature
END as nature
	 

, ST_Transform(ST_Buffer(ST_UNION(geom), 12.5 , 'endcap=flat join=round'),2154) as geom from bdtopo.troncon_ferree
 where nature in ('Voie ferrée principale','Tramway','LGV','Métro')
 and etat_de_l_objet = 'En service'
 group by nature
 ;
 
 alter table bdtopo.trains_buffer add primary key(id);
 
  

update bdtopo.trains_buffer set geom = st_makevalid(geom);
update bdtopo.trains_buffer set geom = st_simplify(geom,1.0);


-- OPTIMIZATION 1: Create proper indexes (run these once)
-- Spatial index on trains_buffer geometry
CREATE INDEX IF NOT EXISTS idx_trains_buffer_geom_gist ON bdtopo.trains_buffer USING GIST (geom);
