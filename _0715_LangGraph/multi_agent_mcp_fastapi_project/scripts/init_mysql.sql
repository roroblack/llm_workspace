CREATE DATABASE IF NOT EXISTS multi_agent_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'multi_agent_user'@'localhost' IDENTIFIED BY 'multi_agent_password';
CREATE USER IF NOT EXISTS 'multi_agent_user'@'%' IDENTIFIED BY 'multi_agent_password';
GRANT ALL PRIVILEGES ON multi_agent_db.* TO 'multi_agent_user'@'localhost';
GRANT ALL PRIVILEGES ON multi_agent_db.* TO 'multi_agent_user'@'%';
FLUSH PRIVILEGES;
