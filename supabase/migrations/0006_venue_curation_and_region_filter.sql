-- Idempotent. Venue aliases/TM IDs, hide out-of-area venues, per-source geo filter.
insert into venues (slug,name,metro,region,city,state,tm_venue_id,source_kind,aliases,is_active) values
('marymoor-park','Marymoor Park','seattle','eastside','Redmond','WA','KovZpa3qwe','ticketmaster',array['Marymoor Live - Presented By Toyota','Marymoor Live'],true),
('chateau-ste-michelle','Chateau Ste. Michelle','seattle','eastside','Woodinville','WA','KovZpZAFkkJA','ticketmaster',array['Chateau Ste Michelle Winery'],true),
('benaroya-hall','Benaroya Hall (Seattle Symphony)','seattle','core','Seattle','WA','Z7r9jZadcG','ticketmaster',array['Taper Auditorium','Benaroya Hall - S. Mark Taper Auditorium'],true),
('tulalip-resort-casino','Tulalip Resort Casino','everett','north','Tulalip','WA','KovZpZAaaEvA','ticketmaster',array['Tulalip Amphitheatre'],true),
('skagit-valley-casino','Skagit Valley Casino Resort','bellingham','north','Bow','WA','KovZpa3r8e','ticketmaster',array['Skagit Valley Casino Pacific Showroom'],true),
('gorge-amphitheatre','Gorge Amphitheatre','seattle','central wa','George','WA','KovZpZAEkk1A','ticketmaster',array['Gorge Amphitheatre','The Gorge','Gorge Amphitheatre at George'],true),
('taproot-theatre','Taproot Theatre','seattle','core','Seattle','WA','ZFr9jZe66d','ticketmaster',array['Taproot Theatre'],true),
('act-theatre','ACT Theatre','seattle','core','Seattle','WA','ZAr9jZ1e-x','ticketmaster',array['ACT Theatre','A Contemporary Theatre'],true),
('5th-avenue-theatre','The 5th Avenue Theatre','seattle','core','Seattle','WA','KovZpa3Mze','ticketmaster',array['The 5th Avenue Theatre','5th Avenue Theatre'],true),
('bagley-wright-theatre','Bagley Wright Theatre','seattle','core','Seattle','WA','Z6r9jZedae','ticketmaster',array['Bagley Wright Theatre'],true),
('woodland-park-zoo','Woodland Park Zoo','seattle','core','Seattle','WA','ZFr9jZd16d','ticketmaster',array['Woodland Park Zoo','ZooTunes'],true),
('fisher-pavilion','Fisher Pavilion at Seattle Center','seattle','core','Seattle','WA','KovZpZAdAnkA','ticketmaster',array['Fisher Pavilion At Seattle Center'],true),
('madame-lous','Madame Lou''s','seattle','core','Seattle','WA','Z7r9jZa7L0','ticketmaster',array['Madame Lou''s'],true),
('q-nightclub','Q Nightclub','seattle','core','Seattle','WA','Z7r9jZadV7','ticketmaster',array['Q Nightclub'],true),
('rialto-theater-tacoma','Rialto Theater','tacoma','core','Tacoma','WA','KovZpa3zee','ticketmaster',array['Rialto Theater'],true),
('dune-peninsula','Dune Peninsula','tacoma','core','Tacoma','WA','Z7r9jZaAQw','ticketmaster',array['Dune Peninsula'],true),
('airport-tavern-tacoma','Airport Tavern','tacoma','core','Tacoma','WA','Z7r9jZad23','ticketmaster',array['Airport Tavern'],true),
('theatre-on-the-square','Theatre on the Square','tacoma','core','Tacoma','WA','KovZpZA1tlaA','ticketmaster',array['Theatre On the Square'],true),
('victory-hall-boxyard','Victory Hall at The Boxyard','tacoma','core','Tacoma','WA','Z7r9jZaAqC','ticketmaster',array['Victory Hall at The Boxyard'],true),
('washington-state-fair','Washington State Fair','tacoma','puyallup','Puyallup','WA','ZFr9jZe7FA','ticketmaster',array['Washington State Fair'],true),
('outlet-collection-seattle','The Outlet Collection Seattle','seattle','south','Auburn','WA','Z7r9jZaAkR','ticketmaster',array['The Outlet Collection Seattle'],true),
('muckleshoot-casino','Muckleshoot Casino Events Center','seattle','south','Auburn','WA','KovZ917AJEj','ticketmaster',array['Muckleshoot Casino Events Center'],true),
('federal-way-paec','Federal Way PAEC','seattle','south','Federal Way','WA','Z7r9jZadKL','ticketmaster',array['Federal Way PAEC','Federal Way Performing Arts and Event Center'],true),
('remlinger-farms','Remlinger Farms','seattle','eastside','Carnation','WA','KovZ917AioZ','ticketmaster',array['Remlinger Farms'],true),
('apex-everett','APEX Everett','everett','core','Everett','WA','KovZ917Am28','ticketmaster',array['APEX Everett'],true),
('clearwater-casino-suquamish','Clearwater Casino Resort','seattle','kitsap','Suquamish','WA','KovZ917ALUH','ticketmaster',array['Suquamish Clearwater Beach Rock Music & Sports Lounge','Suquamish Clearwater Resort Lawn','Suquamish Clearwater Casino Event Center','Clearwater Casino Resort'],true),
('kiana-lodge','Kiana Lodge','seattle','kitsap','Poulsbo','WA','KovZ917AJ9G','ticketmaster',array['Kiana Lodge'],true),
('admiral-theatre-bremerton','Admiral Theatre','seattle','kitsap','Bremerton','WA','ZFr9jZkF6a','ticketmaster',array['Admiral Theatre - WA','Admiral Theatre'],true),
('knitting-factory-spokane','Knitting Factory - Spokane','eastern_wa','spokane','Spokane','WA','KovZ917AJvZ','ticketmaster',array['Knitting Factory - Spokane'],false),
('becu-live-northern-quest','BECU Live at Northern Quest','eastern_wa','spokane','Airway Heights','WA','KovZ917AiIF','ticketmaster',array['BECU Live at Northern Quest'],false),
('northern-quest-casino','Northern Quest Resort and Casino','eastern_wa','spokane','Airway Heights','WA','KovZpZAIv7JA','ticketmaster',array['Northern Quest Resort and Casino'],false),
('toyota-center-kennewick','Toyota Center Kennewick','eastern_wa','tri-cities','Kennewick','WA','KovZpa34pe','ticketmaster',array['Toyota Center Kennewick'],false),
('legends-casino','Legends Casino Event Center','eastern_wa','yakima','Toppenish','WA','KovZpZAFFEeA','ticketmaster',array['Legends Casino Event Center'],false),
('martin-woldson-fox','Martin Woldson Theater at the Fox','eastern_wa','spokane','Spokane','WA','KovZ917A53V','ticketmaster',array['Martin Woldson Theater at the Fox'],false),
('one-spokane-stadium','One Spokane Stadium','eastern_wa','spokane','Spokane','WA','KovZ917ARuj','ticketmaster',array['One Spokane Stadium'],false),
('bing-crosby-theater','Bing Crosby Theater','eastern_wa','spokane','Spokane','WA','KovZ917A2d7','ticketmaster',array['Bing Crosby Theater'],false),
('numerica-veterans-arena','Numerica Veterans Arena','eastern_wa','yakima','Yakima','WA','KovZpZA1eklA','ticketmaster',array['Numerica Veterans Arena'],false)
on conflict (slug) do update set
  aliases=excluded.aliases, tm_venue_id=excluded.tm_venue_id, is_active=excluded.is_active;

create or replace view public_events as
 select e.id,e.title,e.headliner,e.lineup,e.description,e.category,e.genres,e.starts_at,e.doors_at,e.ends_at,e.date_local,e.is_all_ages,e.is_free,e.price_min,e.price_max,e.currency,e.status,e.onsale_at,e.presale_at,e.ticket_url,e.ticket_url_type,e.image_url,e.source_url,e.source_slug,e.first_seen,
   v.id as venue_id,v.name as venue_name,v.slug as venue_slug,v.metro,v.region,v.city,v.state,v.lat,v.lng,v.website as venue_website
  from events e join venues v on v.id=e.venue_id
 where e.status <> 'cancelled'::text and e.date_local >= current_date and v.is_active;

update sources set config = config || jsonb_build_object(
  'geo_filter', jsonb_build_object('center_lat',47.6062,'center_lng',-122.3321,'max_miles',130,'keep_tm_venue_ids',jsonb_build_array('KovZpZAEkk1A')))
where slug='ticketmaster_seatac';
