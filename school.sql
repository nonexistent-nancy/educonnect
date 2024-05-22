CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    privilege TEXT NOT NULL,
    school_id INTEGER NOT NULL,
    grade_identifier TEXT,
    display_name TEXT,

    FOREIGN KEY(school_id) REFERENCES school_configuration(id)
);

CREATE TABLE grade(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assigned_at INTEGER NOT NULL,
    value INTEGER NOT NULL,
    assigned_to INTEGER,
    subject INTEGER,
    FOREIGN KEY(assigned_to) REFERENCES user(id),
    FOREIGN KEY(subject) REFERENCES subject(id)
);




CREATE TABLE subject(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullName TEXT NOT NULL,
    shortName TEXT NOT NULL,
    teacher INTEGER,
    FOREIGN KEY(teacher) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS _transaction(
    id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    label TEXT NOT NULL,
    before TEXT NOT NULL,
    after TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    disputed BOOLEAN NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);


CREATE TABLE IF NOT EXISTS school_configuration(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    website TEXT NOT NULL,
    logo TEXT,

    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS oauth_sessions(
    client_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    token_expires INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_codes(
    code TEXT NOT NULL,
    client_id TEXT NOT NULL,
    user_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_apps(
    id INTEGER,
    name TEXT NOT NULL,
    client_id TEXT NOT NULL,
    client_secret TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    scope TEXT NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES user(id)
);