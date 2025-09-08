/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.11-MariaDB, for debian-linux-gnu (aarch64)
--
-- Host: localhost    Database: rfid_inventory
-- ------------------------------------------------------
-- Server version	10.11.11-MariaDB-0+deb12u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bi_executive_kpis`
--

DROP TABLE IF EXISTS `bi_executive_kpis`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bi_executive_kpis` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `period_ending` date NOT NULL,
  `period_type` varchar(20) NOT NULL DEFAULT 'WEEKLY',
  `total_revenue` decimal(15,2) DEFAULT NULL,
  `rental_revenue` decimal(15,2) DEFAULT NULL,
  `revenue_growth_pct` decimal(5,2) DEFAULT NULL,
  `gross_margin_pct` decimal(5,2) DEFAULT NULL,
  `ebitda_margin_pct` decimal(5,2) DEFAULT NULL,
  `labor_cost_ratio` decimal(5,2) DEFAULT NULL,
  `store_rankings` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`store_rankings`)),
  `best_performing_store` varchar(10) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_period_type` (`period_ending`,`period_type`),
  KEY `ix_period_ending` (`period_ending`),
  KEY `ix_period_type` (`period_type`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bi_executive_kpis`
--

LOCK TABLES `bi_executive_kpis` WRITE;
/*!40000 ALTER TABLE `bi_executive_kpis` DISABLE KEYS */;
INSERT INTO `bi_executive_kpis` VALUES
(1,'2025-08-27','WEEKLY',125000.00,98000.00,12.50,65.00,25.00,0.18,NULL,'3607','2025-08-27 22:52:28','2025-08-27 22:52:28'),
(2,'2025-08-20','WEEKLY',118000.00,92000.00,8.20,64.50,24.80,0.19,NULL,'6800','2025-08-27 22:52:28','2025-08-27 22:52:28'),
(3,'2025-08-13','WEEKLY',115000.00,89000.00,5.10,63.80,23.50,0.20,NULL,'3607','2025-08-27 22:52:28','2025-08-27 22:52:28');
/*!40000 ALTER TABLE `bi_executive_kpis` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bi_operational_scorecard`
--

DROP TABLE IF EXISTS `bi_operational_scorecard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bi_operational_scorecard` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `week_ending` date NOT NULL,
  `store_code` varchar(10) NOT NULL,
  `new_contracts_count` int(11) DEFAULT NULL,
  `reservation_pipeline_14d` decimal(12,2) DEFAULT NULL,
  `reservation_pipeline_total` decimal(12,2) DEFAULT NULL,
  `ar_over_45_days_pct` decimal(5,2) DEFAULT NULL,
  `discount_total` decimal(12,2) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_week_store` (`week_ending`,`store_code`),
  KEY `ix_week_ending` (`week_ending`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bi_operational_scorecard`
--

LOCK TABLES `bi_operational_scorecard` WRITE;
/*!40000 ALTER TABLE `bi_operational_scorecard` DISABLE KEYS */;
/*!40000 ALTER TABLE `bi_operational_scorecard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bi_store_performance`
--

DROP TABLE IF EXISTS `bi_store_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `bi_store_performance` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `period_ending` date NOT NULL,
  `store_code` varchar(10) NOT NULL,
  `period_type` varchar(20) NOT NULL DEFAULT 'BIWEEKLY',
  `rental_revenue` decimal(15,2) DEFAULT NULL,
  `total_revenue` decimal(15,2) DEFAULT NULL,
  `payroll_cost` decimal(15,2) DEFAULT NULL,
  `wage_hours` decimal(10,2) DEFAULT NULL,
  `labor_cost_ratio` decimal(5,2) DEFAULT NULL,
  `revenue_per_hour` decimal(10,2) DEFAULT NULL,
  `avg_wage_rate` decimal(8,2) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_period_store` (`period_ending`,`store_code`,`period_type`),
  KEY `ix_period_store` (`period_ending`,`store_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bi_store_performance`
--

LOCK TABLES `bi_store_performance` WRITE;
/*!40000 ALTER TABLE `bi_store_performance` DISABLE KEYS */;
/*!40000 ALTER TABLE `bi_store_performance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `business_context_knowledge`
--

DROP TABLE IF EXISTS `business_context_knowledge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `business_context_knowledge` (
  `knowledge_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `context_type` varchar(50) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `store_id` varchar(10) DEFAULT NULL,
  `region` varchar(100) DEFAULT NULL,
  `applies_globally` tinyint(1) DEFAULT NULL,
  `seasonal_pattern` varchar(100) DEFAULT NULL,
  `time_period_start` date DEFAULT NULL,
  `time_period_end` date DEFAULT NULL,
  `recurrence_pattern` varchar(100) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `impact_description` text DEFAULT NULL,
  `quantitative_impact` decimal(10,2) DEFAULT NULL,
  `data_sources` text DEFAULT NULL,
  `historical_examples` text DEFAULT NULL,
  `confidence_level` int(11) DEFAULT NULL,
  `user_id` varchar(100) NOT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `user_role` varchar(100) DEFAULT NULL,
  `local_expertise_years` int(11) DEFAULT NULL,
  `submitted_date` datetime DEFAULT NULL,
  `validated_by` varchar(100) DEFAULT NULL,
  `validation_date` datetime DEFAULT NULL,
  `times_referenced` int(11) DEFAULT NULL,
  `usefulness_score` decimal(3,2) DEFAULT NULL,
  PRIMARY KEY (`knowledge_id`),
  KEY `idx_context_store` (`store_id`),
  KEY `idx_context_type` (`context_type`),
  KEY `idx_context_category` (`category`),
  KEY `idx_context_date` (`submitted_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `business_context_knowledge`
--

LOCK TABLES `business_context_knowledge` WRITE;
/*!40000 ALTER TABLE `business_context_knowledge` DISABLE KEYS */;
/*!40000 ALTER TABLE `business_context_knowledge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `business_intelligence_config`
--

DROP TABLE IF EXISTS `business_intelligence_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `business_intelligence_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) NOT NULL DEFAULT 'default_user',
  `config_name` varchar(100) NOT NULL DEFAULT 'default',
  `revenue_target_monthly` float DEFAULT 100000,
  `revenue_target_quarterly` float DEFAULT 300000,
  `revenue_target_yearly` float DEFAULT 1200000,
  `inventory_turnover_target` float DEFAULT 6,
  `profit_margin_target` float DEFAULT 0.25,
  `customer_satisfaction_target` float DEFAULT 0.85,
  `benchmark_industry_avg_enabled` tinyint(1) DEFAULT 1,
  `benchmark_historical_enabled` tinyint(1) DEFAULT 1,
  `benchmark_competitor_enabled` tinyint(1) DEFAULT 0,
  `roi_calculation_period` varchar(20) DEFAULT 'quarterly',
  `roi_include_overhead` tinyint(1) DEFAULT 1,
  `roi_include_labor_costs` tinyint(1) DEFAULT 1,
  `roi_discount_rate` float DEFAULT 0.08,
  `resale_min_profit_margin` float DEFAULT 0.15,
  `resale_max_age_months` int(11) DEFAULT 24,
  `resale_condition_threshold` float DEFAULT 7,
  `resale_demand_threshold` float DEFAULT 0.3,
  `performance_alert_threshold` float DEFAULT 0.8,
  `critical_alert_threshold` float DEFAULT 0.6,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_config` (`user_id`,`config_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `business_intelligence_config`
--

LOCK TABLES `business_intelligence_config` WRITE;
/*!40000 ALTER TABLE `business_intelligence_config` DISABLE KEYS */;
INSERT INTO `business_intelligence_config` VALUES
(1,'default_user','default',100000,300000,1200000,6,0.25,0.85,1,1,0,'quarterly',1,1,0.08,0.15,24,7,0.3,0.8,0.6,1,'2025-08-29 18:45:59','2025-08-29 18:45:59');
/*!40000 ALTER TABLE `business_intelligence_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `configuration_audit`
--

DROP TABLE IF EXISTS `configuration_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `configuration_audit` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) NOT NULL,
  `config_type` varchar(50) NOT NULL,
  `config_id` int(11) NOT NULL,
  `action` varchar(20) NOT NULL,
  `old_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`old_values`)),
  `new_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`new_values`)),
  `change_reason` text DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(500) DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_user_config` (`user_id`,`config_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `configuration_audit`
--

LOCK TABLES `configuration_audit` WRITE;
/*!40000 ALTER TABLE `configuration_audit` DISABLE KEYS */;
INSERT INTO `configuration_audit` VALUES
(1,'default_user','prediction_parameters',1,'update',NULL,'{\"forecast_weekly_enabled\": true}',NULL,'127.0.0.1','curl/7.88.1','2025-08-29 23:47:47'),
(2,'default_user','prediction_parameters',1,'update',NULL,'{\"forecast_horizons\": {\"weekly\": true, \"monthly\": true, \"quarterly\": true, \"yearly\": true}, \"confidence_intervals\": {\"80\": true, \"90\": true, \"95\": false, \"default\": 90}, \"external_factors\": {\"seasonality\": 0.4, \"trend\": 0.3, \"economic\": 0.2, \"promotional\": 0.1}, \"thresholds\": {\"low_stock\": 0.2, \"high_stock\": 2, \"demand_spike\": 1.5}, \"store_specific\": {\"enabled\": true, \"mappings\": {}}}',NULL,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36','2025-08-29 23:48:23');
/*!40000 ALTER TABLE `configuration_audit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contract_snapshots`
--

DROP TABLE IF EXISTS `contract_snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `contract_snapshots` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `contract_number` varchar(255) NOT NULL,
  `tag_id` varchar(255) NOT NULL,
  `client_name` varchar(255) DEFAULT NULL,
  `common_name` varchar(255) DEFAULT NULL,
  `rental_class_num` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `quality` varchar(50) DEFAULT NULL,
  `bin_location` varchar(255) DEFAULT NULL,
  `serial_number` varchar(255) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `snapshot_date` datetime NOT NULL,
  `snapshot_type` varchar(50) NOT NULL,
  `created_by` varchar(255) DEFAULT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_contract_snapshots_tag_id` (`tag_id`),
  KEY `ix_contract_snapshots_snapshot_date` (`snapshot_date`),
  KEY `ix_contract_snapshots_contract_number` (`contract_number`)
) ENGINE=InnoDB AUTO_INCREMENT=320 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contract_snapshots`
--

LOCK TABLES `contract_snapshots` WRITE;
/*!40000 ALTER TABLE `contract_snapshots` DISABLE KEYS */;
INSERT INTO `contract_snapshots` VALUES
(1,'L26','300F4F573AD003C09282A894','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(2,'L26','300F4F573AD003C09282A8A8','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(3,'L26','300F4F573AD003C092CC1ED7','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(4,'L26','300F4F573AD003C092CC1ED9','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(5,'L26','300F4F573AD003C092CC1EF7','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(6,'L26','300F4F573AD003C092CC1F01','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(7,'L26','300F4F573AD003C092CC1F10','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(8,'L26','300F4F573AD003C192860004','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(9,'L26','300F4F573AD003C192CA0839','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(10,'L26','300F4F573AD003C192CC0233','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(11,'L26','300F4F573AD003C192CC0237','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(12,'L26','33155C66A40000000009379E','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(13,'L26','33155C66A4000000000937C1','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(14,'L26','33155C66A4000000000937C4','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-24 22:22:33','manual','user',45.114861,-93.276815),
(15,'L25','222211110999','LAUNDRY ','90X156 BLACK LINEN ROUNDED CORNER','62236','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114798,-93.276778),
(16,'L25','300C0639399005C255C1BD30','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','A+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(17,'L25','300C0639399005C255C1BD59','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','A+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(18,'L25','300C0639399005C255C1BD65','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','A+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(19,'L25','300F4F573AD0004043E86DD7','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(20,'L25','300F4F573AD0004043E86E0C','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(21,'L25','300F4F573AD0004043E86E50','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(22,'L25','300F4F573AD0004043E86E68','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(23,'L25','300F4F573AD0004043E86E7F','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(24,'L25','300F4F573AD003C092807815','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(25,'L25','300F4F573AD003C09295538C','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(26,'L25','300F4F573AD003C092AC616E','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(27,'L25','300F4F573AD003C092AC617E','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(28,'L25','300F4F573AD003C092AC6190','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(29,'L25','300F4F573AD003C092AE6F54','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(30,'L25','300F4F573AD003C092AE6FC6','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(31,'L25','300F4F573AD003C092AE6FD0','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(32,'L25','300F4F573AD003C092D48092','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(33,'L25','300F4F573AD003C092D480DB','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(34,'L25','300F4F573AD003C092D48109','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(35,'L25','300F4F573AD003C19292001B','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(36,'L25','300F4F573AD003C1929A0023','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(37,'L25','300F4F573AD003C1929A0028','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(38,'L25','300F4F573AD003C192B6000B','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(39,'L25','300F4F573AD003C192B6002D','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(40,'L25','300F4F573AD003C2524E66ED','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(41,'L25','300F4F573AD003C2524E671E','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(42,'L25','30651484B80A680445FF6938','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(43,'L25','323232323131313130303033','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(44,'L25','323232323131313130303039','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(45,'L25','323232323131313130303131','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(46,'L25','323232323131313130303133','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(47,'L25','323232323131313130303135','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(48,'L25','323232323131313130303235','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(49,'L25','323232323131313130303236','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(50,'L25','323232323131313130303237','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(51,'L25','323232323131313130303437','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(52,'L25','323232323131313130303530','LAUNDRY ','120 ROUND  WHITE LINEN','61930','On Rent','B+','NR5x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(53,'L25','323232323131313131313934','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(54,'L25','323232323131313131343330','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(55,'L25','323232323131313131343334','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(56,'L25','323232323131313131343336','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(57,'L25','323232323131313131343338','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(58,'L25','323232323131313131343339','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(59,'L25','323232323131313131343436','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(60,'L25','323232323131313131343437','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(61,'L25','323232323131313131343438','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(62,'L25','323232323131313131343439','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(63,'L25','323232323131313131343532','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(64,'L25','323232323131313131343533','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(65,'L25','323232323131313131343534','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(66,'L25','323232323131313131353736','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(67,'L25','323232323131313131353738','LAUNDRY ','90X156  WHITE LINEN ROUNDED CORNE','62235','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(68,'L25','323232323131313132303035','LAUNDRY ','90X156 BLACK LINEN ROUNDED CORNER','62236','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114798,-93.276778),
(69,'L25','33155C66A4000000000936FF','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(70,'L25','33155C66A400000000093711','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(71,'L25','33155C66A400000000093744','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(72,'L25','33155C66A40000000009379C','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(73,'L25','33155C66A4000000000937A0','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(74,'L25','33155C66A4000000000937AA','LAUNDRY ','108 ROUND WHITE LINEN','61885','On Rent','B+','NR3x1',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(75,'L25','35FFFFFFF5E6023B759C29F0','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(76,'L25','35FFFFFFF7BBAD353CBC4A02','LAUNDRY ','90 ROUND BLACK LINEN','61826','On Rent','B','NR5x2',NULL,'L6','2025-08-24 22:22:55','manual','user',45.114616,-93.276713),
(77,'L25','39307831353620424C41434B','LAUNDRY ','90X156 BLACK LINEN ROUNDED CORNER','62236','On Rent','B+','NR3x2',NULL,NULL,'2025-08-24 22:22:55','manual','user',45.114798,-93.276778),
(78,'L26','300F4F573AD003C09282A894','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(79,'L26','300F4F573AD003C09282A8A8','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(80,'L26','300F4F573AD003C092CC1ED7','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(81,'L26','300F4F573AD003C092CC1ED9','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(82,'L26','300F4F573AD003C092CC1EF7','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(83,'L26','300F4F573AD003C092CC1F01','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(84,'L26','300F4F573AD003C092CC1F10','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(85,'L26','300F4F573AD003C192860004','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(86,'L26','300F4F573AD003C192CA0839','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(87,'L26','300F4F573AD003C192CC0233','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(88,'L26','300F4F573AD003C192CC0237','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(89,'L26','33155C66A40000000009379E','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(90,'L26','33155C66A4000000000937C1','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(91,'L26','33155C66A4000000000937C4','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 15:05:05','manual','user',45.114861,-93.276815),
(92,'L26','300F4F573AD003C09282A894','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(93,'L26','300F4F573AD003C09282A8A8','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(94,'L26','300F4F573AD003C092CC1ED7','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(95,'L26','300F4F573AD003C092CC1ED9','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(96,'L26','300F4F573AD003C092CC1EF7','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(97,'L26','300F4F573AD003C092CC1F01','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(98,'L26','300F4F573AD003C092CC1F10','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(99,'L26','300F4F573AD003C192860004','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(100,'L26','300F4F573AD003C192CA0839','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(101,'L26','300F4F573AD003C192CC0233','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(102,'L26','300F4F573AD003C192CC0237','LAUNDRY ','60X120  WHITE LINEN','62088','On Rent','B+','NR4x1',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(103,'L26','33155C66A40000000009379E','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(104,'L26','33155C66A4000000000937C1','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(105,'L26','33155C66A4000000000937C4','LAUNDRY ','90 ROUND PEACH LINEN','61836','On Rent','A-','NR5x2',NULL,NULL,'2025-08-25 20:04:15','manual','user',45.114861,-93.276815),
(106,'223587','E2801191A50300608D122A4A','DAVIS','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','Ready to Rent','B','',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',NULL,NULL),
(107,'223587','E2801191A50300608D13058A','DAVIS','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','Ready to Rent','B','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',NULL,NULL),
(108,'223587','E2801191A50300608D17202A','DAVIS','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','Ready to Rent','B','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',NULL,NULL),
(109,'223587','E2801191A50300608D17854A','DAVIS','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','Ready to Rent','B','',NULL,'215190','2025-08-29 12:00:03','periodic','scheduled_task',NULL,NULL),
(110,'L9','222211111479','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(111,'L9','300C0639399005C255C1BB41','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(112,'L9','300C0639399005C255C1BB5C','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(113,'L9','300C0639399005C255C1BCFE','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(114,'L9','300C0639399005C255C1BD3B','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(115,'L9','300C0639399005C255C1BD45','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(116,'L9','300F4F573AD003C08F6FF88F','LAUNDRY ','60X120 RED LINEN','62104','On Rent','A-','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(117,'L9','300F4F573AD003C09280782C','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(118,'L9','300F4F573AD003C09282A8BA','LAUNDRY ','90 ROUND PASTEL PINK LINEN','61846','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(119,'L9','300F4F573AD003C09282AAA6','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(120,'L9','300F4F573AD003C0929123A8','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','B+','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(121,'L9','300F4F573AD003C092CC1EC7','LAUNDRY ','60X120 ORANGE LINEN','62101','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(122,'L9','300F4F573AD003C092CC1EDB','LAUNDRY ','60X120 ORANGE LINEN','62101','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(123,'L9','300F4F573AD003C18F76000D','LAUNDRY ','60X120 RED LINEN','62104','On Rent','A-','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(124,'L9','300F4F573AD003C18F760062','LAUNDRY ','60X120 RED LINEN','62104','On Rent','A-','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(125,'L9','300F4F573AD003C1914A013F','LAUNDRY ','90 ROUND  WHITE LINEN','61825','On Rent','B','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(126,'L9','300F4F573AD003C192800088','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(127,'L9','300F4F573AD003C192840014','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(128,'L9','300F4F573AD003C192860001','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(129,'L9','300F4F573AD003C2524C60DD','LAUNDRY ','60X120 BYZANTINE FALL GOLD LINEN','62098','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(130,'L9','300F4F573AD003C2524C60F5','LAUNDRY ','60X120 BLACK LINEN','62089','On Rent','B','NR4x1',NULL,'L6','2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(131,'L9','300F4F573AD003C2524C6124','LAUNDRY ','60X120 BLACK LINEN','62089','On Rent','B','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(132,'L9','300F4F573AD003C2524C6198','LAUNDRY ','60X120 BYZANTINE FALL GOLD LINEN','62098','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(133,'L9','300F4F573AD003C2524E6668','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','A','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(134,'L9','300F4F573AD003C2524E668F','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','A','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(135,'L9','300F4F573AD003C2524E66C5','LAUNDRY ','132 ROUND BLACK  LINEN','61982','On Rent','A','NR2x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(136,'L9','323232323131313130343133','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(137,'L9','323232323131313130343135','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.115049,-93.276548),
(138,'L9','323232323131313130343139','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(139,'L9','323232323131313130343232','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'216252','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(140,'L9','323232323131313130343234','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(141,'L9','323232323131313130343236','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.115049,-93.276548),
(142,'L9','323232323131313130343237','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(143,'L9','323232323131313130343337','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(144,'L9','323232323131313130343339','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.115049,-93.276548),
(145,'L9','323232323131313130343430','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(146,'L9','323232323131313130343431','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(147,'L9','323232323131313130343432','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(148,'L9','323232323131313130343433','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(149,'L9','323232323131313130343434','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(150,'L9','323232323131313130343435','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(151,'L9','323232323131313130343437','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(152,'L9','323232323131313130343530','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114983,-93.276610),
(153,'L9','323232323131313130343634','LAUNDRY ','132 ROUND BLACK  LINEN','61982','On Rent','B+','NR2x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(154,'L9','323232323131313130343636','LAUNDRY ','132 ROUND BLACK  LINEN','61982','On Rent','B+','NR2x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(155,'L9','323232323131313130343637','LAUNDRY ','132 ROUND BLACK  LINEN','61982','On Rent','B+','NR2x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(156,'L9','323232323131313130383835','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(157,'L9','323232323131313130383836','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(158,'L9','323232323131313130383837','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(159,'L9','323232323131313130383838','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(160,'L9','323232323131313130383839','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(161,'L9','323232323131313130393833','LAUNDRY ','90X156 BLACK LINEN ROUNDED CORNER','62236','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(162,'L9','323232323131313131313933','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.115049,-93.276548),
(163,'L9','323232323131313131323032','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','B+','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(164,'L9','323232323131313131343138','LAUNDRY ','108 ROUND BYZANTINE FALL GOLD','72595','On Rent','B','NA',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(165,'L9','323232323131313131343139','LAUNDRY ','108 ROUND BYZANTINE FALL GOLD','72595','On Rent','B','NA',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(166,'L9','323232323131313131343230','LAUNDRY ','108 ROUND BYZANTINE FALL GOLD','72595','On Rent','B','NA',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(167,'L9','323232323131313131343831','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(168,'L9','323232323131313131343833','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(169,'L9','323232323131313131343835','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(170,'L9','323232323131313131343836','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(171,'L9','323232323131313131373036','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(172,'L9','323232323131313131373037','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(173,'L9','323232323131313131373038','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(174,'L9','323232323131313131373039','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(175,'L9','323232323131313131373133','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(176,'L9','323232323131313131373138','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(177,'L9','323232323131313131373139','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(178,'L9','323232323131313131373230','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(179,'L9','323232323131313131373231','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(180,'L9','323232323131313131373232','LAUNDRY ','54 SQUARE BLACK LINEN','62292','On Rent','A-','NR4x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(181,'L9','323232323131313230343134','LAUNDRY ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.115049,-93.276548),
(182,'L9','323332323131313131343738','LAUNDRY ','90X132 BLACK LINEN ROUNDED CORNER','62188','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(183,'L9','33155C66A40000000009371E','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(184,'L9','33155C66A400000000093724','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(185,'L9','33155C66A400000000093759','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','B','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(186,'L9','33155C66A400000000093779','LAUNDRY ','90 ROUND RED LINEN','61840','On Rent','A-','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114868,-93.276615),
(187,'L9','33155C66A40000000009377B','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','B','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(188,'L9','33155C66A4000000000937A7','LAUNDRY ','108 ROUND BLACK LINEN','61886','On Rent','B','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114778,-93.276731),
(189,'223836','E2009A9110003AF000002923','BLAINE VILL','HOTDOG STEAMER','3727','Needs to be Inspected','B+','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114869,-93.276826),
(190,'218616','3035307B2831B383E243EF17','PTC','TOP HP 20 X 20 (G1)','65367','On Rent','A','MR4J2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(191,'218616','3035307B2831B383E243F027','PTC','TOP HP 10 X 20 (G2)','62707','On Rent','B','MR4H2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(192,'218616','3035307B2831B383E26D77A7','PTC','TOP HP 10 x 20 (G1)','65119','On Rent','B','MR4G2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(193,'218616','3035307B2831B383E34B014C','PTC','TOP HP 20 X 20 (G1)','65367','On Rent','B+','MR4J2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(194,'218616','3035307B2831B383E34B017B','PTC','TOP HP 20 X 20 (G1)','65367','On Rent','A','MR4J2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(195,'218616','3035307B2831B383E34B0181','PTC','TOP HP 20 X 20 (G1)','65367','On Rent','A','MR4J2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(196,'218616','3035307B2831B383E34B023F','PTC','TOP HP 20 X 20 (G1)','65367','On Rent','A-','MR4J2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(197,'221862','222211110080524F59414C20','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(198,'221862','300F4F573AD003C08F69ED62','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(199,'221862','300F4F573AD003C08F69ED95','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(200,'221862','300F4F573AD003C08F69ED9A','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(201,'221862','300F4F573AD003C08F69EDBA','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,'Test','2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(202,'221862','300F4F573AD003C08F69EDBC','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(203,'221862','300F4F573AD003C08F69EDBE','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(204,'221862','300F4F573AD003C08F69EDC5','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,'Test','2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(205,'221862','300F4F573AD003C08F69EDEB','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(206,'221862','300F4F573AD003C08F69EE08','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(207,'221862','300F4F573AD003C08F6FF8DD','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(208,'221862','300F4F573AD003C08F74891F','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(209,'221862','300F4F573AD003C08F748921','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(210,'221862','300F4F573AD003C0928F0E5F','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(211,'221862','300F4F573AD003C0929B7DDC','MISSISSIPPI','90 ROUND NAVY BLUE LINEN','61866','On Rent','B+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(212,'221862','300F4F573AD003C0929B7DEE','MISSISSIPPI','90 ROUND NAVY BLUE LINEN','61866','On Rent','B+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(213,'221862','300F4F573AD003C0929B7DF6','MISSISSIPPI','90 ROUND NAVY BLUE LINEN','61866','On Rent','B+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(214,'221862','300F4F573AD003C0929B7E19','MISSISSIPPI','90 ROUND NAVY BLUE LINEN','61866','On Rent','B+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(215,'221862','300F4F573AD003C18F760001','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(216,'221862','300F4F573AD003C18F760004','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,'Test','2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(217,'221862','300F4F573AD003C18F76003A','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(218,'221862','300F4F573AD003C1914A00F4','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(219,'221862','323232323131313130303737','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(220,'221862','323232323131313130303738','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(221,'221862','323232323131313130303831','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(222,'221862','323232323131313130303834','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(223,'221862','323232323131313130303835','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(224,'221862','323232323131313130303836','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(225,'221862','323232323131313130303937','MISSISSIPPI','120 ROUND ROYAL BLUE LINEN','61960','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(226,'221862','323232323131313131333533','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(227,'221862','323232323131313131333534','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(228,'221862','323232323131313131333535','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(229,'221862','323232323131313131333536','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(230,'221862','323232323131313131333537','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(231,'221862','323232323131313131333538','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(232,'221862','323232323131313131333539','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(233,'221862','323232323131313131333633','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(234,'221862','323232323131313131333634','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(235,'221862','323232323131313131333635','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(236,'221862','323232323131313131333636','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(237,'221862','323232323131313131333637','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(238,'221862','323232323131313131333638','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(239,'221862','323232323131313131333639','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(240,'221862','323232323131313131333730','MISSISSIPPI','108 ROUND NAVY BLUE LINEN','61924','On Rent','A-','NR3x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(241,'221862','33155C66A400000000093738','MISSISSIPPI','90 ROUND NAVY BLUE LINEN','61866','On Rent','B+','NR5x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(242,'221862','35FFFFFFF1031DC63A46A670','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(243,'221862','35FFFFFFF433EA27BF750B5F','MISSISSIPPI','60X120 ROYAL BLUE LINEN','62121','On Rent','B+','NR4x1',NULL,'Test','2025-08-29 12:00:03','periodic','scheduled_task',0.000000,0.000000),
(244,'223527','300C0639399005C255C1BD6B','NORTHSIDE ','CARPET RUNNER, RED 4 X 25 (G2)','63328','Needs to be Inspected','A','MR1F2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',NULL,NULL),
(245,'223527','300C0639399005C255C1BD7F','NORTHSIDE ','CARPET RUNNER, RED 4 X 25 (G1)','63327','Needs to be Inspected','B','MR1F2',NULL,'.','2025-08-29 12:00:03','periodic','scheduled_task',NULL,NULL),
(246,'224070','003232323231313131303034','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(247,'224070','300C0639399005C255C1BCBD','NOOR ','90X132  WHITE LINEN ROUNDED CORNE','62187','On Rent','A+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114826,-93.276845),
(248,'224070','300C0639399005C255C1BCC7','NOOR ','90X132  WHITE LINEN ROUNDED CORNE','62187','On Rent','A+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114826,-93.276845),
(249,'224070','300C0639399005C255C1BCFC','NOOR ','90X132  WHITE LINEN ROUNDED CORNE','62187','On Rent','A+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114826,-93.276845),
(250,'224070','300C0639399005C255C1BD3E','NOOR ','CARPET RUNNER, RED 4 X 50 (G2)','63330','On Rent','A','MR1F2',NULL,'','2025-08-29 12:00:03','periodic','scheduled_task',45.114820,-93.276902),
(251,'224070','323232323131313130313839','NOOR ','120 ROUND MAGENTA LINEN','61951','On Rent','A-','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(252,'224070','323232323131313130313930','NOOR ','120 ROUND MAGENTA LINEN','61951','On Rent','A-','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(253,'224070','323232323131313130313931','NOOR ','120 ROUND MAGENTA LINEN','61951','On Rent','A-','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(254,'224070','323232323131313130323938','NOOR ','120 ROUND EGGPLANT LINEN','61957','On Rent','B+','NR5x1',NULL,'L6','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(255,'224070','323232323131313130333030','NOOR ','120 ROUND EGGPLANT LINEN','61957','On Rent','B+','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(256,'224070','323232323131313130333032','NOOR ','120 ROUND EGGPLANT LINEN','61957','On Rent','B+','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(257,'224070','323232323131313130333033','NOOR ','120 ROUND EGGPLANT LINEN','61957','On Rent','B+','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(258,'224070','323232323131313130333134','NOOR ','120 ROUND EGGPLANT LINEN','61957','On Rent','B+','NR5x1',NULL,'L6','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(259,'224070','323232323131313130343031','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(260,'224070','323232323131313130343032','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(261,'224070','323232323131313130343033','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(262,'224070','323232323131313130343131','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(263,'224070','323232323131313130343132','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(264,'224070','323232323131313130343230','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(265,'224070','323232323131313130343231','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(266,'224070','323232323131313130343233','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(267,'224070','323232323131313130343238','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(268,'224070','323232323131313130343239','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(269,'224070','323232323131313130343330','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(270,'224070','323232323131313130343331','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(271,'224070','323232323131313130343332','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(272,'224070','323232323131313130343333','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(273,'224070','323232323131313130343334','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(274,'224070','323232323131313130343335','NOOR ','120 ROUND BLACK LINEN','61931','On Rent','B','NR5x1',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(275,'224070','323232323131313132303030','NOOR ','90X156 BLACK LINEN ROUNDED CORNER','62236','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(276,'224070','323232323131313132303031','NOOR ','90X156 BLACK LINEN ROUNDED CORNER','62236','On Rent','B+','NR3x2',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(277,'224070','323232323131323130363835','NOOR ','132 ROUND MAGENTA LINEN','62004','On Rent','B+','NR2x1',NULL,'L6','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(278,'224070','323232323131323130363837','NOOR ','132 ROUND MAGENTA LINEN','62004','On Rent','B+','NR2x1',NULL,'L6','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(279,'224070','323232323131323130363838','NOOR ','132 ROUND MAGENTA LINEN','62004','On Rent','B+','NR2x1',NULL,'L6','2025-08-29 12:00:03','periodic','scheduled_task',45.114842,-93.276877),
(280,'224222','E2801191A50300608D128F1A','JENKINS ','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','On Rent','B','',NULL,'Tim','2025-08-29 12:00:03','periodic','scheduled_task',45.114963,-93.276817),
(281,'224222','E2801191A50300608D13EFBA','JENKINS ','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','On Rent','B','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114963,-93.276817),
(282,'224222','E2801191A50300608D14859A','JENKINS ','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','On Rent','B','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114963,-93.276817),
(283,'224222','E2801191A50300608D156F5B','JENKINS ','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','On Rent','B+','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114963,-93.276817),
(284,'224222','E2801191A50300608D156FCA','JENKINS ','TOP, TABLE ROUND, 30 INCH PLYWOOD','63131','On Rent','B','',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.114963,-93.276817),
(285,'224047','425445000000000000000004','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(286,'224047','425445000000000000000005','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent','','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(287,'224047','425445000000000000000006','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent','','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(288,'224047','425445000000000000000061','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(289,'224047','425445000000000000000062','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(290,'224047','425445000000000000000064','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent','','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(291,'224047','425445000000000000000215','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(292,'224047','425445000000000000000216','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(293,'224047','425445000000000000000217','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(294,'224047','425445000000000000000218','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(295,'224047','425445000000000000000219','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(296,'224047','425445000000000000000220','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(297,'224047','425445000000000000000221','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(298,'224047','425445000000000000000222','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(299,'224047','425445000000000000000223','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(300,'224047','425445000000000000000224','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(301,'224047','425445000000000000000225','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(302,'224047','425445000000000000000226','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(303,'224047','425445000000000000000227','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(304,'224047','425445000000000000000228','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(305,'224047','425445000000000000000229','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(306,'224047','425445000000000000000251','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(307,'224047','425445000000000000000252','GRILL','FLATWARE FORK, DINNER (10 PACK)','65698','On Rent',NULL,'pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(308,'224047','726573616C6501628662746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(309,'224047','726573616C6501628762746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(310,'224047','726573616C6501628862746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(311,'224047','726573616C6501628962746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(312,'224047','726573616C6501630362746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(313,'224047','726573616C6501630662746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(314,'224047','726573616C6501630762746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(315,'224047','726573616C6501630862746500000000','GRILL','CHINA PLATE, IMPERIAL DINNER 10 in(5) PACK','65091','On Rent','A','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(316,'224047','726573616C6501911362746500000000','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent','B','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(317,'224047','726573616C6501911462746500000000','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent','B','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(318,'224047','726573616C6501911562746500000000','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent','B','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189),
(319,'224047','726573616C6501911662746500000000','GRILL','CHINA PLATE, WHITE DINNER 10.5 in (5)PACK','65096','On Rent','B','pack',NULL,NULL,'2025-08-29 12:00:03','periodic','scheduled_task',45.115575,-93.277189);
/*!40000 ALTER TABLE `contract_snapshots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `correlation_audit_log`
--

DROP TABLE IF EXISTS `correlation_audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `correlation_audit_log` (
  `audit_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `table_name` varchar(100) DEFAULT NULL,
  `record_id` bigint(20) DEFAULT NULL,
  `action` varchar(20) DEFAULT NULL,
  `old_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`old_values`)),
  `new_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`new_values`)),
  `changed_fields` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`changed_fields`)),
  `changed_by` varchar(100) DEFAULT NULL,
  `changed_date` datetime DEFAULT NULL,
  `change_source` varchar(50) DEFAULT NULL,
  `session_id` varchar(100) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`audit_id`),
  KEY `idx_audit_date` (`changed_date`),
  KEY `idx_audit_table` (`table_name`),
  KEY `idx_audit_user` (`changed_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `correlation_audit_log`
--

LOCK TABLES `correlation_audit_log` WRITE;
/*!40000 ALTER TABLE `correlation_audit_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `correlation_audit_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `correlation_feedback`
--

DROP TABLE IF EXISTS `correlation_feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `correlation_feedback` (
  `feedback_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `correlation_id` varchar(100) DEFAULT NULL,
  `prediction_id` varchar(100) DEFAULT NULL,
  `feedback_type` enum('CORRELATION_RATING','PREDICTION_VALIDATION','BUSINESS_CONTEXT','CORRELATION_SUGGESTION','DATA_SOURCE_SUGGESTION') NOT NULL,
  `status` enum('SUBMITTED','UNDER_REVIEW','IMPLEMENTED','REJECTED','ARCHIVED') DEFAULT NULL,
  `user_id` varchar(100) NOT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `user_role` varchar(100) DEFAULT NULL,
  `relevance_rating` int(11) DEFAULT NULL,
  `accuracy_rating` int(11) DEFAULT NULL,
  `usefulness_rating` int(11) DEFAULT NULL,
  `thumbs_up_down` tinyint(1) DEFAULT NULL,
  `confidence_level` int(11) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `comments` text DEFAULT NULL,
  `business_context` text DEFAULT NULL,
  `suggested_improvements` text DEFAULT NULL,
  `submitted_date` datetime DEFAULT NULL,
  `updated_date` datetime DEFAULT NULL,
  `reviewed_by` varchar(100) DEFAULT NULL,
  `reviewed_date` datetime DEFAULT NULL,
  `admin_notes` text DEFAULT NULL,
  `implementation_notes` text DEFAULT NULL,
  `context_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`context_data`)),
  PRIMARY KEY (`feedback_id`),
  KEY `idx_feedback_correlation` (`correlation_id`),
  KEY `idx_feedback_status` (`status`),
  KEY `idx_feedback_type` (`feedback_type`),
  KEY `idx_feedback_user` (`user_id`),
  KEY `idx_feedback_date` (`submitted_date`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `correlation_feedback`
--

LOCK TABLES `correlation_feedback` WRITE;
/*!40000 ALTER TABLE `correlation_feedback` DISABLE KEYS */;
INSERT INTO `correlation_feedback` VALUES
(1,'external-factors-analysis',NULL,'CORRELATION_RATING','SUBMITTED','demo_user_elwksan6h','Demo User','Store Manager',4,3,3,1,4,NULL,'','not just weddings but also yard and tree cleanup',NULL,'2025-08-31 06:26:46','2025-08-31 06:26:46',NULL,NULL,NULL,NULL,'{\"page\": \"/predictive/analytics\", \"timestamp\": \"2025-08-31T06:26:43.341Z\"}');
/*!40000 ALTER TABLE `correlation_feedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `correlation_settings`
--

DROP TABLE IF EXISTS `correlation_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `correlation_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) NOT NULL DEFAULT 'default_user',
  `setting_name` varchar(100) NOT NULL DEFAULT 'default',
  `min_correlation_weak` float DEFAULT 0.3,
  `min_correlation_moderate` float DEFAULT 0.5,
  `min_correlation_strong` float DEFAULT 0.7,
  `p_value_threshold` float DEFAULT 0.05,
  `confidence_level` float DEFAULT 0.95,
  `max_lag_periods` int(11) DEFAULT 12,
  `min_lag_periods` int(11) DEFAULT 1,
  `default_lag_period` int(11) DEFAULT 3,
  `economic_factors_enabled` tinyint(1) DEFAULT 1,
  `seasonal_factors_enabled` tinyint(1) DEFAULT 1,
  `promotional_factors_enabled` tinyint(1) DEFAULT 1,
  `weather_factors_enabled` tinyint(1) DEFAULT 0,
  `auto_correlation_enabled` tinyint(1) DEFAULT 1,
  `cross_correlation_enabled` tinyint(1) DEFAULT 1,
  `partial_correlation_enabled` tinyint(1) DEFAULT 0,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_setting` (`user_id`,`setting_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `correlation_settings`
--

LOCK TABLES `correlation_settings` WRITE;
/*!40000 ALTER TABLE `correlation_settings` DISABLE KEYS */;
INSERT INTO `correlation_settings` VALUES
(1,'default_user','default',0.3,0.5,0.7,0.05,0.95,12,1,3,1,1,1,0,1,1,0,1,'2025-08-29 18:42:01','2025-08-29 18:42:01');
/*!40000 ALTER TABLE `correlation_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `correlation_suggestions`
--

DROP TABLE IF EXISTS `correlation_suggestions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `correlation_suggestions` (
  `suggestion_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `suggestion_type` varchar(50) DEFAULT NULL,
  `status` enum('SUBMITTED','UNDER_REVIEW','IMPLEMENTED','REJECTED','ARCHIVED') DEFAULT NULL,
  `priority_score` int(11) DEFAULT NULL,
  `user_id` varchar(100) NOT NULL,
  `user_name` varchar(255) DEFAULT NULL,
  `user_role` varchar(100) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `description` text NOT NULL,
  `business_justification` text DEFAULT NULL,
  `expected_impact` varchar(20) DEFAULT NULL,
  `proposed_factor_1` varchar(255) DEFAULT NULL,
  `proposed_factor_2` varchar(255) DEFAULT NULL,
  `expected_relationship` varchar(100) DEFAULT NULL,
  `suggested_data_source` varchar(255) DEFAULT NULL,
  `estimated_effort` varchar(20) DEFAULT NULL,
  `required_resources` text DEFAULT NULL,
  `implementation_timeline` varchar(50) DEFAULT NULL,
  `upvotes` int(11) DEFAULT NULL,
  `downvotes` int(11) DEFAULT NULL,
  `submitted_date` datetime DEFAULT NULL,
  `reviewed_date` datetime DEFAULT NULL,
  `reviewed_by` varchar(100) DEFAULT NULL,
  `implementation_date` datetime DEFAULT NULL,
  `admin_notes` text DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL,
  PRIMARY KEY (`suggestion_id`),
  KEY `idx_suggestion_type` (`suggestion_type`),
  KEY `idx_suggestion_priority` (`priority_score`),
  KEY `idx_suggestion_date` (`submitted_date`),
  KEY `idx_suggestion_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `correlation_suggestions`
--

LOCK TABLES `correlation_suggestions` WRITE;
/*!40000 ALTER TABLE `correlation_suggestions` DISABLE KEYS */;
/*!40000 ALTER TABLE `correlation_suggestions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `data_integration_settings`
--

DROP TABLE IF EXISTS `data_integration_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `data_integration_settings` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) NOT NULL DEFAULT 'default_user',
  `setting_name` varchar(100) NOT NULL DEFAULT 'default',
  `csv_auto_import_enabled` tinyint(1) DEFAULT 0,
  `csv_import_frequency` varchar(20) DEFAULT 'daily',
  `csv_import_time` varchar(8) DEFAULT '02:00:00',
  `csv_backup_enabled` tinyint(1) DEFAULT 1,
  `csv_validation_strict` tinyint(1) DEFAULT 1,
  `api_timeout_seconds` int(11) DEFAULT 30,
  `api_retry_attempts` int(11) DEFAULT 3,
  `api_rate_limit_enabled` tinyint(1) DEFAULT 1,
  `api_rate_limit_requests` int(11) DEFAULT 100,
  `api_rate_limit_window` int(11) DEFAULT 3600,
  `real_time_refresh_enabled` tinyint(1) DEFAULT 0,
  `refresh_interval_minutes` int(11) DEFAULT 15,
  `background_refresh_enabled` tinyint(1) DEFAULT 1,
  `data_quality_checks_enabled` tinyint(1) DEFAULT 1,
  `missing_data_threshold` float DEFAULT 0.1,
  `outlier_detection_enabled` tinyint(1) DEFAULT 1,
  `outlier_detection_method` varchar(20) DEFAULT 'iqr',
  `max_file_size_mb` int(11) DEFAULT 50,
  `supported_formats` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT '["csv", "xlsx", "json"]' CHECK (json_valid(`supported_formats`)),
  `archive_processed_files` tinyint(1) DEFAULT 1,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_setting` (`user_id`,`setting_name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `data_integration_settings`
--

LOCK TABLES `data_integration_settings` WRITE;
/*!40000 ALTER TABLE `data_integration_settings` DISABLE KEYS */;
INSERT INTO `data_integration_settings` VALUES
(1,'default_user','default',0,'daily','02:00:00',1,1,30,3,1,100,3600,0,15,1,1,0.1,1,'iqr',50,'[\"csv\", \"xlsx\", \"json\"]',1,1,'2025-08-29 18:45:59','2025-08-29 18:45:59');
/*!40000 ALTER TABLE `data_integration_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `data_quality_metrics`
--

DROP TABLE IF EXISTS `data_quality_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `data_quality_metrics` (
  `metric_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `correlation_id` bigint(20) DEFAULT NULL,
  `issue_type` varchar(20) DEFAULT NULL,
  `severity` varchar(20) DEFAULT NULL,
  `source_system` varchar(50) DEFAULT NULL,
  `field_name` varchar(100) DEFAULT NULL,
  `expected_value` text DEFAULT NULL,
  `actual_value` text DEFAULT NULL,
  `resolution_status` varchar(20) DEFAULT NULL,
  `resolution_method` varchar(100) DEFAULT NULL,
  `resolved_date` datetime DEFAULT NULL,
  `resolved_by` varchar(100) DEFAULT NULL,
  `affected_records` int(11) DEFAULT NULL,
  `business_impact` varchar(255) DEFAULT NULL,
  `detected_date` datetime DEFAULT NULL,
  `detection_method` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`metric_id`),
  KEY `idx_quality_status` (`resolution_status`),
  KEY `idx_quality_correlation` (`correlation_id`),
  KEY `idx_quality_severity` (`severity`),
  CONSTRAINT `data_quality_metrics_ibfk_1` FOREIGN KEY (`correlation_id`) REFERENCES `inventory_correlation_master` (`correlation_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `data_quality_metrics`
--

LOCK TABLES `data_quality_metrics` WRITE;
/*!40000 ALTER TABLE `data_quality_metrics` DISABLE KEYS */;
/*!40000 ALTER TABLE `data_quality_metrics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `equipment_performance_view`
--

DROP TABLE IF EXISTS `equipment_performance_view`;
