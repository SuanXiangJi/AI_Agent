/*
 Navicat Premium Data Transfer

 Source Server         : MySql_localhost_3306
 Source Server Type    : MySQL
 Source Server Version : 50737
 Source Host           : localhost:3306
 Source Schema         : agent

 Target Server Type    : MySQL
 Target Server Version : 50737
 File Encoding         : 65001

 Date: 06/05/2025 00:11:41
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for tasks
-- ----------------------------
DROP TABLE IF EXISTS `tasks`;
CREATE TABLE `tasks`  (
  `task_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '任务的唯一标识符，自增主键。',
  `user_id` int(11) NOT NULL COMMENT '关联的用户 ID，外键关联 users 表的 id 字段。',
  `task_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '任务的名称，不能为空。',
  `task_description` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '任务的详细描述。',
  `status` int(11) NULL DEFAULT 0 COMMENT '任务状态，暂时保留，后期根据需要具体定义。',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '任务创建的时间戳，默认值为当前时间。',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '任务更新的时间戳，每次更新记录时自动更新。',
  `is_deleted` int(1) UNSIGNED ZEROFILL NULL DEFAULT NULL,
  PRIMARY KEY (`task_id`) USING BTREE,
  INDEX `user_id`(`user_id`) USING BTREE,
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 113 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
