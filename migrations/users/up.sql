CREATE TABLE users (
    user_id BIGINT NOT NULL,
    coins INT DEFAULT 0 NOT NULL,
    birthday VARCHAR(20) DEFAULT NULL,
    lottery_guess INT DEFAULT NULL,
    starboard_count INT DEFAULT 0 NOT NULL,
    bump_amount INT DEFAULT 0,
    rate_limits JSON DEFAULT NULL,
    star_time INT DEFAULT NULL,
    PRIMARY KEY (user_id)
);