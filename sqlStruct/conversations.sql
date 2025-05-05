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

 Date: 06/05/2025 00:11:32
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for conversations
-- ----------------------------
DROP TABLE IF EXISTS `conversations`;
CREATE TABLE `conversations`  (
  `conversation_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '对话记录的唯一标识符，自增主键。',
  `task_id` int(11) NOT NULL COMMENT '关联的任务 ID，外键关联 tasks 表的 task_id 字段。',
  `user_id` int(11) NOT NULL COMMENT '用户 ID，外键关联 users 表的 id 字段。',
  `result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '消息内容。',
  `sent_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息发送的时间戳，默认值为当前时间。',
  `keywords` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '关键词，每次对话中的核心内容提取到此处。',
  `is_ai` tinyint(4) NULL DEFAULT NULL COMMENT '用于区分是AI发出的还是用户发出的消息。',
  `memory` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `gif` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `links` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
  `is_deleted` int(1) UNSIGNED ZEROFILL NULL DEFAULT NULL,
  PRIMARY KEY (`conversation_id`) USING BTREE,
  INDEX `task_id`(`task_id`) USING BTREE,
  INDEX `conversations_ibfk_2`(`user_id`) USING BTREE,
  CONSTRAINT `conversations_ibfk_1` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `conversations_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 250 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
