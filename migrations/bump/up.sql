CREATE TABLE bump (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    bump_time BIGINT NOT NULL,
    PRIMARY KEY (id)
);