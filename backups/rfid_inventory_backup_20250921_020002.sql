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
-- Table structure for table `business_analytics_configuration`
--

DROP TABLE IF EXISTS `business_analytics_configuration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `business_analytics_configuration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(50) NOT NULL DEFAULT 'default_user',
  `config_name` varchar(100) NOT NULL DEFAULT 'default',
  `equipment_underperformer_threshold` decimal(10,2) DEFAULT 50.00,
  `low_turnover_threshold` decimal(10,2) DEFAULT 25.00,
  `high_value_threshold` decimal(10,2) DEFAULT 500.00,
  `low_usage_threshold` decimal(10,2) DEFAULT 100.00,
  `resale_priority_threshold` decimal(10,2) DEFAULT 10.00,
  `ar_aging_low_threshold` decimal(5,2) DEFAULT 5.00,
  `ar_aging_medium_threshold` decimal(5,2) DEFAULT 15.00,
  `revenue_concentration_risk_threshold` decimal(5,3) DEFAULT 0.400,
  `declining_trend_threshold` decimal(5,3) DEFAULT -0.100,
  `minimum_data_points_correlation` int(11) DEFAULT 10,
  `confidence_threshold` decimal(5,3) DEFAULT 0.950,
  `store_specific_thresholds` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`store_specific_thresholds`)),
  `enable_underperformance_alerts` tinyint(1) DEFAULT 1,
  `enable_high_value_alerts` tinyint(1) DEFAULT 1,
  `enable_ar_aging_alerts` tinyint(1) DEFAULT 1,
  `enable_concentration_risk_alerts` tinyint(1) DEFAULT 1,
  `alert_frequency` varchar(20) DEFAULT 'weekly',
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_config` (`user_id`,`config_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `business_analytics_configuration`
--

LOCK TABLES `business_analytics_configuration` WRITE;
/*!40000 ALTER TABLE `business_analytics_configuration` DISABLE KEYS */;
/*!40000 ALTER TABLE `business_analytics_configuration` ENABLE KEYS */;
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
-- Temporary table structure for view `combined_inventory`
--

DROP TABLE IF EXISTS `combined_inventory`;
