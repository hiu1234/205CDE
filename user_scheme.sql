create table user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,username varuint8_t(1024) NOT NULL,password varuint8_t(1024) NOT NULL);
create table role(role_id INTEGER PRIMARY KEY AUTOINCREMENT,role_name varuint8_t(1024) not null);
create table link_user_role(user_id INTEGER NOT NULL,role_id INTEGER NOT NULL,PRIMARY KEY(user_id,role_id),FOREIGN KEY(user_id) REFERENCES user(user_id),FOREIGN KEY(role_id) REFERENCES role(role_id));
insert into user (username,password) select "abc","1234";
insert into role (role_name) select "admin";
insert into role (role_name) select "user";
insert into link_user_role(user_id,role_id) select 1,1;