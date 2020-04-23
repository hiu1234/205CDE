create table catalog(catalog_id INTEGER PRIMARY KEY AUTOINCREMENT,catalog_name varuint8_t(1024));
create table song (song_id  INTEGER PRIMARY KEY AUTOINCREMENT ,path varuint8_t(2048),title varuint8_t(400),track tinyint,duration INTEGER,price INTEGER);
create table album (album_id  INTEGER PRIMARY KEY AUTOINCREMENT ,album_name varuint8_t(1024), image varuint8_t(2048));
create table artist (artist_id  INTEGER PRIMARY KEY AUTOINCREMENT,artist_name varuint8_t(400));
create table link_catalog_album (catalog_id uint32_t not null,album_id uint32_t not null,PRIMARY key(catalog_id, album_id),foreign key(catalog_id)REFERENCES catalog(catalog_id),foreign key(album_id) REFERENCES album(album_id));
create table link_album_artist (album_id uint32_t not null,artist_id uint32_t not null,PRIMARY key(album_id , artist_id),foreign key(album_id) REFERENCES album(album_id),foreign key(artist_id)REFERENCES artist(artist_id));
create table link_album_song (album_id uint32_t not null,song_id uint32_t not null,PRIMARY key(album_id , song_id),foreign key(album_id) REFERENCES album(album_id),foreign key(song_id)REFERENCES song(song_id));
