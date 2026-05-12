CREATE DATABASE IF NOT EXISTS depo_yonetim
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'depo_app'@'%' IDENTIFIED BY 'depo_app_dev';
GRANT ALL PRIVILEGES ON depo_yonetim.* TO 'depo_app'@'%';

CREATE USER IF NOT EXISTS 'depo_ai_reader'@'%' IDENTIFIED BY 'depo_ai_reader_dev';
CREATE USER IF NOT EXISTS 'depo_ai_reader'@'localhost' IDENTIFIED BY 'depo_ai_reader_dev';
GRANT SELECT ON depo_yonetim.* TO 'depo_ai_reader'@'%';
GRANT SELECT ON depo_yonetim.* TO 'depo_ai_reader'@'localhost';

FLUSH PRIVILEGES;
