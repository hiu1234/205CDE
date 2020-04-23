create table sales(user_id INTEGER NOT NULL,song_id INTEGER NOT NULL, purchase_time datetime NOT NULL,PRIMARY KEY(user_id,song_id))
create table credit(user_id INTEGER NOT NULL PRIMARY KEY,credit INTEGER NOT NULL)
insert into credit (user_id,credit) select 1,0;