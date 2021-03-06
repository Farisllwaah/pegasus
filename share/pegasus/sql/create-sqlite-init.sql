--
-- schema: all
-- driver: sqlite sqlite-jdbc-3.7.2.jar
-- $Revision$
--

CREATE TABLE IF NOT EXISTS sequences (
	name		VARCHAR(32) NOT NULL,
	currval		BIGINT DEFAULT 0,

	CONSTRAINT      pk_sequences PRIMARY KEY(name)
);

CREATE TABLE IF NOT EXISTS pegasus_schema (
	name		VARCHAR(64) NOT NULL,
	catalog		VARCHAR(16),
	version		FLOAT,
	creator		VARCHAR(32),
	creation	DATETIME,

	CONSTRAINT	pk_pegasus_schema PRIMARY KEY(name)
);
