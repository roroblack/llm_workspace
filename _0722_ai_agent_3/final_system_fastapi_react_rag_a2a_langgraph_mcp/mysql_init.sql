CREATE DATABASE IF NOT EXISTS `fastapi_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `fastapi_db`;

CREATE TABLE IF NOT EXISTS `customer_complaint` (
    `cc_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `custum_id` VARCHAR(100) NOT NULL,
    `dept_id` VARCHAR(50) NOT NULL,
    `message` TEXT NOT NULL,
    `receipt_status` TINYINT(1) NOT NULL DEFAULT 0,
    `resolution_status` TINYINT(1) NOT NULL DEFAULT 0,
    `inquiry_date` DATETIME(6) NOT NULL,
    `receipt_date` DATETIME(6) NULL,
    `resolution_date` DATETIME(6) NULL,
    PRIMARY KEY (`cc_id`),
    INDEX `ix_customer_complaint_customer` (`custum_id`),
    INDEX `ix_customer_complaint_department_status`
        (`dept_id`, `receipt_status`, `resolution_status`)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
