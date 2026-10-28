-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: claude_runtime
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `config_revisions`
--

DROP TABLE IF EXISTS `config_revisions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `config_revisions` (
  `revision_id` int NOT NULL AUTO_INCREMENT,
  `config_id` int DEFAULT NULL,
  `note` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`revision_id`)
) ENGINE=InnoDB AUTO_INCREMENT=129 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `config_revisions`
--

LOCK TABLES `config_revisions` WRITE;
/*!40000 ALTER TABLE `config_revisions` DISABLE KEYS */;
INSERT INTO `config_revisions` VALUES (1,1,'baseline'),(2,2,'baseline'),(3,3,'baseline'),(4,4,'baseline'),(5,5,'baseline'),(6,6,'baseline'),(7,7,'baseline'),(8,8,'baseline'),(9,9,'baseline'),(10,10,'baseline'),(11,11,'baseline'),(12,12,'baseline'),(13,13,'baseline'),(14,14,'baseline'),(15,15,'baseline'),(16,16,'baseline'),(17,17,'baseline'),(18,18,'baseline'),(19,19,'baseline'),(20,20,'baseline'),(21,21,'baseline'),(22,22,'baseline'),(23,23,'baseline'),(24,24,'baseline'),(25,25,'baseline'),(26,26,'baseline'),(27,27,'baseline'),(28,28,'baseline'),(29,29,'baseline'),(30,30,'baseline'),(31,31,'baseline'),(32,32,'baseline'),(33,33,'baseline'),(34,34,'baseline'),(35,35,'baseline'),(36,36,'baseline'),(37,37,'baseline'),(38,38,'baseline'),(39,39,'baseline'),(40,40,'baseline'),(41,41,'baseline'),(42,42,'baseline'),(43,43,'baseline'),(44,44,'baseline'),(45,45,'baseline'),(46,46,'baseline'),(47,47,'baseline'),(48,48,'baseline'),(49,49,'baseline'),(50,50,'baseline'),(51,51,'baseline'),(52,52,'baseline'),(53,53,'baseline'),(54,54,'baseline'),(55,55,'baseline'),(56,56,'baseline'),(57,57,'baseline'),(58,58,'baseline'),(59,59,'baseline'),(60,60,'baseline'),(61,61,'baseline'),(62,62,'baseline'),(63,63,'baseline'),(64,64,'baseline'),(65,65,'baseline'),(66,66,'baseline'),(67,67,'baseline'),(68,68,'baseline'),(69,69,'baseline'),(70,70,'baseline'),(71,71,'baseline'),(72,72,'baseline'),(73,73,'baseline'),(74,74,'baseline'),(75,75,'baseline'),(76,76,'baseline'),(77,77,'baseline'),(78,78,'baseline'),(79,79,'baseline'),(80,80,'baseline'),(81,81,'baseline'),(82,82,'baseline'),(83,83,'baseline'),(84,84,'baseline'),(85,85,'baseline'),(86,86,'baseline'),(87,87,'baseline'),(88,88,'baseline'),(89,89,'baseline'),(90,90,'baseline'),(91,91,'baseline'),(92,92,'baseline'),(93,93,'baseline'),(94,94,'baseline'),(95,95,'baseline'),(96,96,'baseline'),(97,97,'baseline'),(98,98,'baseline'),(99,99,'baseline'),(100,100,'baseline'),(101,101,'baseline'),(102,102,'baseline'),(103,103,'baseline'),(104,104,'baseline'),(105,105,'baseline'),(106,106,'baseline'),(107,107,'baseline'),(108,108,'baseline'),(109,109,'baseline'),(110,110,'baseline'),(111,111,'baseline'),(112,112,'baseline'),(113,113,'baseline'),(114,114,'baseline'),(115,115,'baseline'),(116,116,'baseline'),(117,117,'baseline'),(118,118,'baseline'),(119,119,'baseline'),(120,120,'baseline'),(121,121,'baseline'),(122,122,'baseline'),(123,123,'baseline'),(124,124,'baseline'),(125,125,'baseline'),(126,126,'baseline'),(127,127,'baseline'),(128,128,'baseline');
/*!40000 ALTER TABLE `config_revisions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `runtime_config`
--

DROP TABLE IF EXISTS `runtime_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `runtime_config` (
  `id` int NOT NULL,
  `environment` varchar(16) DEFAULT NULL,
  `config_key` varchar(64) DEFAULT NULL,
  `revision` int DEFAULT NULL,
  `config_value` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `runtime_config`
--

LOCK TABLES `runtime_config` WRITE;
/*!40000 ALTER TABLE `runtime_config` DISABLE KEYS */;
INSERT INTO `runtime_config` VALUES (1,'production','setting_1',1,'{\"seed\":1}'),(2,'production','setting_2',1,'{\"seed\":2}'),(3,'production','setting_3',1,'{\"seed\":3}'),(4,'production','setting_4',2,'{\"updated_by\": \"deploy_agent\", \"version\": 4}'),(5,'production','setting_5',2,'{\"updated_by\": \"deploy_agent\", \"version\": 5}'),(6,'production','setting_6',2,'{\"updated_by\": \"deploy_agent\", \"version\": 6}'),(7,'production','setting_7',1,'{\"seed\":7}'),(8,'production','setting_8',1,'{\"seed\":8}'),(9,'production','setting_9',1,'{\"seed\":9}'),(10,'production','setting_10',1,'{\"seed\":10}'),(11,'production','setting_11',1,'{\"seed\":11}'),(12,'production','setting_12',1,'{\"seed\":12}'),(13,'production','setting_13',1,'{\"seed\":13}'),(14,'production','setting_14',1,'{\"seed\":14}'),(15,'production','setting_15',1,'{\"seed\":15}'),(16,'production','setting_16',1,'{\"seed\":16}'),(17,'production','setting_17',1,'{\"seed\":17}'),(18,'production','setting_18',2,'{\"updated_by\": \"deploy_agent\", \"version\": 18}'),(19,'production','setting_19',2,'{\"updated_by\": \"deploy_agent\", \"version\": 19}'),(20,'production','setting_20',1,'{\"seed\":20}'),(21,'production','setting_21',1,'{\"seed\":21}'),(22,'production','setting_22',1,'{\"seed\":22}'),(23,'production','setting_23',1,'{\"seed\":23}'),(24,'production','setting_24',1,'{\"seed\":24}'),(25,'production','setting_25',1,'{\"seed\":25}'),(26,'production','setting_26',1,'{\"seed\":26}'),(27,'production','setting_27',1,'{\"seed\":27}'),(28,'production','setting_28',1,'{\"seed\":28}'),(29,'production','setting_29',1,'{\"seed\":29}'),(30,'production','setting_30',1,'{\"seed\":30}'),(31,'production','setting_31',2,'{\"updated_by\": \"deploy_agent\", \"version\": 31}'),(32,'production','setting_32',2,'{\"updated_by\": \"deploy_agent\", \"version\": 32}'),(33,'production','setting_33',2,'{\"updated_by\": \"deploy_agent\", \"version\": 33}'),(34,'production','setting_34',2,'{\"updated_by\": \"deploy_agent\", \"version\": 34}'),(35,'production','setting_35',2,'{\"updated_by\": \"deploy_agent\", \"version\": 35}'),(36,'production','setting_36',1,'{\"seed\":36}'),(37,'production','setting_37',1,'{\"seed\":37}'),(38,'production','setting_38',1,'{\"seed\":38}'),(39,'production','setting_39',1,'{\"seed\":39}'),(40,'production','setting_40',1,'{\"seed\":40}'),(41,'production','setting_41',1,'{\"seed\":41}'),(42,'production','setting_42',1,'{\"seed\":42}'),(43,'production','setting_43',1,'{\"seed\":43}'),(44,'production','setting_44',1,'{\"seed\":44}'),(45,'production','setting_45',1,'{\"seed\":45}'),(46,'production','setting_46',1,'{\"seed\":46}'),(47,'production','setting_47',1,'{\"seed\":47}'),(48,'production','setting_48',1,'{\"seed\":48}'),(49,'production','setting_49',1,'{\"seed\":49}'),(50,'production','setting_50',1,'{\"seed\":50}'),(51,'production','setting_51',1,'{\"seed\":51}'),(52,'production','setting_52',1,'{\"seed\":52}'),(53,'production','setting_53',1,'{\"seed\":53}'),(54,'production','setting_54',1,'{\"seed\":54}'),(55,'production','setting_55',1,'{\"seed\":55}'),(56,'production','setting_56',1,'{\"seed\":56}'),(57,'production','setting_57',1,'{\"seed\":57}'),(58,'production','setting_58',1,'{\"seed\":58}'),(59,'production','setting_59',1,'{\"seed\":59}'),(60,'production','setting_60',1,'{\"seed\":60}'),(61,'production','setting_61',1,'{\"seed\":61}'),(62,'production','setting_62',1,'{\"seed\":62}'),(63,'production','setting_63',1,'{\"seed\":63}'),(64,'production','setting_64',1,'{\"seed\":64}'),(65,'production','setting_65',1,'{\"seed\":65}'),(66,'production','setting_66',1,'{\"seed\":66}'),(67,'production','setting_67',1,'{\"seed\":67}'),(68,'production','setting_68',1,'{\"seed\":68}'),(69,'production','setting_69',1,'{\"seed\":69}'),(70,'production','setting_70',1,'{\"seed\":70}'),(71,'production','setting_71',1,'{\"seed\":71}'),(72,'production','setting_72',1,'{\"seed\":72}'),(73,'production','setting_73',1,'{\"seed\":73}'),(74,'production','setting_74',1,'{\"seed\":74}'),(75,'production','setting_75',1,'{\"seed\":75}'),(76,'production','setting_76',1,'{\"seed\":76}'),(77,'production','setting_77',1,'{\"seed\":77}'),(78,'production','setting_78',1,'{\"seed\":78}'),(79,'production','setting_79',1,'{\"seed\":79}'),(80,'production','setting_80',1,'{\"seed\":80}'),(81,'production','setting_81',1,'{\"seed\":81}'),(82,'production','setting_82',1,'{\"seed\":82}'),(83,'production','setting_83',1,'{\"seed\":83}'),(84,'production','setting_84',1,'{\"seed\":84}'),(85,'production','setting_85',1,'{\"seed\":85}'),(86,'production','setting_86',1,'{\"seed\":86}'),(87,'production','setting_87',1,'{\"seed\":87}'),(88,'production','setting_88',1,'{\"seed\":88}'),(89,'production','setting_89',1,'{\"seed\":89}'),(90,'production','setting_90',1,'{\"seed\":90}'),(91,'production','setting_91',1,'{\"seed\":91}'),(92,'production','setting_92',1,'{\"seed\":92}'),(93,'production','setting_93',1,'{\"seed\":93}'),(94,'production','setting_94',1,'{\"seed\":94}'),(95,'production','setting_95',1,'{\"seed\":95}'),(96,'production','setting_96',1,'{\"seed\":96}'),(97,'staging','setting_97',1,'{\"seed\":97}'),(98,'staging','setting_98',1,'{\"seed\":98}'),(99,'staging','setting_99',1,'{\"seed\":99}'),(100,'staging','setting_100',1,'{\"seed\":100}'),(101,'staging','setting_101',1,'{\"seed\":101}'),(102,'staging','setting_102',1,'{\"seed\":102}'),(103,'staging','setting_103',1,'{\"seed\":103}'),(104,'staging','setting_104',1,'{\"seed\":104}'),(105,'staging','setting_105',1,'{\"seed\":105}'),(106,'staging','setting_106',1,'{\"seed\":106}'),(107,'staging','setting_107',1,'{\"seed\":107}'),(108,'staging','setting_108',1,'{\"seed\":108}'),(109,'staging','setting_109',1,'{\"seed\":109}'),(110,'staging','setting_110',1,'{\"seed\":110}'),(111,'staging','setting_111',1,'{\"seed\":111}'),(112,'staging','setting_112',1,'{\"seed\":112}'),(113,'staging','setting_113',1,'{\"seed\":113}'),(114,'staging','setting_114',1,'{\"seed\":114}'),(115,'staging','setting_115',1,'{\"seed\":115}'),(116,'staging','setting_116',1,'{\"seed\":116}'),(117,'staging','setting_117',1,'{\"seed\":117}'),(118,'staging','setting_118',1,'{\"seed\":118}'),(119,'staging','setting_119',1,'{\"seed\":119}'),(120,'staging','setting_120',1,'{\"seed\":120}'),(121,'staging','setting_121',1,'{\"seed\":121}'),(122,'staging','setting_122',1,'{\"seed\":122}'),(123,'staging','setting_123',1,'{\"seed\":123}'),(124,'staging','setting_124',1,'{\"seed\":124}'),(125,'staging','setting_125',1,'{\"seed\":125}'),(126,'staging','setting_126',1,'{\"seed\":126}'),(127,'staging','setting_127',1,'{\"seed\":127}'),(128,'staging','setting_128',1,'{\"seed\":128}');
/*!40000 ALTER TABLE `runtime_config` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-03 12:04:36
