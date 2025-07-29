-- phpMyAdmin SQL Dump
-- version 5.2.1deb3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jul 29, 2025 at 12:59 PM
-- Server version: 8.0.42-0ubuntu0.24.04.1
-- PHP Version: 8.3.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `school`
--

-- --------------------------------------------------------

--
-- Table structure for table `absence_requests`
--

CREATE TABLE `absence_requests` (
  `id` int NOT NULL,
  `student_id` int NOT NULL,
  `class_id` int NOT NULL,
  `description` text NOT NULL,
  `image_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `attendance_current`
--

CREATE TABLE `attendance_current` (
  `student_id` int NOT NULL,
  `present` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `attendance_current`
--

INSERT INTO `attendance_current` (`student_id`, `present`) VALUES
(24, 0),
(25, 0),
(26, 0),
(27, 0),
(28, 0),
(29, 0),
(30, 0),
(31, 0),
(32, 0),
(45, 0),
(46, 0),
(47, 0),
(48, 0),
(49, 0),
(50, 0),
(51, 0),
(52, 0),
(53, 0),
(54, 0);

-- --------------------------------------------------------

--
-- Table structure for table `attendance_history`
--

CREATE TABLE `attendance_history` (
  `id` int NOT NULL,
  `student_id` int NOT NULL,
  `subject_id` int DEFAULT NULL,
  `absent_date` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `classes`
--

CREATE TABLE `classes` (
  `id` int NOT NULL,
  `name` varchar(20) COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `classes`
--

INSERT INTO `classes` (`id`, `name`) VALUES
(7, '10D'),
(11, '10F'),
(8, '11D'),
(12, '11F'),
(9, '12D'),
(13, '12F'),
(6, '9D'),
(10, '9F');

-- --------------------------------------------------------

--
-- Table structure for table `conduct_grades`
--

CREATE TABLE `conduct_grades` (
  `student_id` int NOT NULL,
  `grade` float NOT NULL DEFAULT '10',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `grades`
--

CREATE TABLE `grades` (
  `id` int NOT NULL,
  `student_id` int NOT NULL,
  `subject` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `grade` float NOT NULL,
  `date_given` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `head_teachers`
--

CREATE TABLE `head_teachers` (
  `id` int NOT NULL,
  `first_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `last_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `class` varchar(20) COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `head_teachers`
--

INSERT INTO `head_teachers` (`id`, `first_name`, `last_name`, `class`) VALUES
(53, 'Adriana', 'Popa', '7'),
(54, 'Gabriel', 'Ionescu', '13');

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `message` text NOT NULL,
  `seen` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `students`
--

CREATE TABLE `students` (
  `id` int NOT NULL,
  `first_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `last_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `photo` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `class_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `students`
--

INSERT INTO `students` (`id`, `first_name`, `last_name`, `photo`, `class_id`, `user_id`) VALUES
(24, 'Razvan', 'Neagu', 'Razvan_Neagu_10D.png', 7, 44),
(25, 'Ana', 'Dobre', 'Ana_Dobre_10D.png', 7, 45),
(26, 'Cristian', 'Pavel', 'Cristian_Pavel_10D.png', 7, 46),
(27, 'Sorina', 'Mihalache', 'Sorina_Mihalache_10D.png', 7, 47),
(28, 'George', 'Tudor', 'George_Tudor_10D.png', 7, 48),
(29, 'Larisa', 'Calin', 'Larisa_Calin_10D.png', 7, 49),
(30, 'Paul', 'Barbu', 'Paul_Barbu_10D.png', 7, 50),
(31, 'Denis', 'Chostache', 'Denis_Chostache_10D.png', 7, 51),
(32, 'Roxana', 'Petrescu', 'Roxana_Petrescu_10D.png', 7, 52),
(45, 'Mihai', 'Trif', 'Mihai_Trif_10D.jpeg', 7, 80),
(46, 'Bianca', 'Ionescu', 'Bianca_Ionescu_12F.png', 13, 82),
(47, 'Darius', 'Lupse', 'Darius_Lupse_12F.jpeg', 13, 83),
(48, 'Darius', 'Nistor', 'Darius_Nistor_12F.png', 13, 84),
(49, 'Ioana', 'Dumitrescu', 'Ioana_Dumitrescu_12F.png', 13, 85),
(50, 'Luca', 'Marinescu', 'Luca_Marinescu_12F.png', 13, 86),
(51, 'Maria', 'Lungu', 'Maria_Lungu_12F.png', 13, 87),
(52, 'Mihai', 'Georgescu', 'Mihai_Georgescu_12F.png', 13, 88),
(53, 'Teodora', 'Enache', 'Teodora_Enache_12F.png', 13, 89),
(54, 'Vlad', 'Radu', 'Vlad_Radu_12F.png', 13, 90);

-- --------------------------------------------------------

--
-- Table structure for table `subjects`
--

CREATE TABLE `subjects` (
  `id` int NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `subjects`
--

INSERT INTO `subjects` (`id`, `name`) VALUES
(10, 'Biologie'),
(9, 'Chimie'),
(8, 'Engleza'),
(4, 'Informatica'),
(7, 'Matematica'),
(5, 'Romana');

-- --------------------------------------------------------

--
-- Table structure for table `teachers`
--

CREATE TABLE `teachers` (
  `id` int NOT NULL,
  `first_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `last_name` varchar(50) COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `teachers`
--

INSERT INTO `teachers` (`id`, `first_name`, `last_name`) VALUES
(53, 'Adriana', 'Popa'),
(54, 'Gabriel', 'Ionescu'),
(55, 'Mihaela', 'Ionescu'),
(56, 'Radu', 'Florescu'),
(57, 'Andreea', 'Muresan'),
(58, 'Claudiu', 'Pavel'),
(59, 'Elena', 'Stoica'),
(60, 'Dan', 'Marinescu');

-- --------------------------------------------------------

--
-- Table structure for table `teacher_assignments`
--

CREATE TABLE `teacher_assignments` (
  `id` int NOT NULL,
  `teacher_id` int NOT NULL,
  `class_id` int NOT NULL,
  `subject_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `teacher_assignments`
--

INSERT INTO `teacher_assignments` (`id`, `teacher_id`, `class_id`, `subject_id`) VALUES
(43, 53, 7, 10),
(45, 53, 13, 10),
(46, 54, 7, 5),
(47, 57, 13, 9),
(48, 54, 13, 5),
(49, 53, 8, 10),
(50, 53, 9, 10),
(51, 54, 8, 9),
(52, 54, 9, 9);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `password` varchar(255) COLLATE utf8mb4_general_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`) VALUES
(1, 'admin', '$2b$12$AYpMcvN5utpNZMrA9qzJuOqZcixsMdbUZptbjLrCIkEVhaILV4I8y'),
(43, 'prof1', '$2b$12$s4HWK/pBjQz5so90812rHO/ph5ZybRjYraJcviIMAO9wEvqhhX7k6'),
(44, 'razvan.neagu', '$2b$12$odFP3McdMjtWsPUvUgarAehBu6v4NXvCTyMfhe1OLhhZwDNvm97j2'),
(45, 'ana.dobre', '$2b$12$04i/iurp0VhLNAzYIX5hY.9rGPfPtRJu/DzWgOonMEO6d4kwffRAe'),
(46, 'cristian.pavel', '$2b$12$zFxS0xq/kEPPmIUXfDfJXO0LWMWetTOJeCntTHSG69iduv.Iqej2S'),
(47, 'sorina.mihalache', '$2b$12$0CytXSK42hrW4HYGbmVzo.o8cEny1Zf/Ic76RPPjZYPaqlJ/kuJBm'),
(48, 'george.tudor', '$2b$12$X8P8jLIbxOmIyicCs5i3UOdd8fwK4qMb/P4lKMIH37UzTb7BS9uWe'),
(49, 'larisa.calin', '$2b$12$vzB2ClGteDx/6T898QVB6OIb8IFXTBlc2Yj17LQU1KpuP3lmz6wsS'),
(50, 'paul.barbu', '$2b$12$XPZDE5m6EjBwDjxddB8scuDx754ugAxmySIM7qr/JVbtWbWDYVGVy'),
(51, 'denis.costache', '$2b$12$BMcom3Gpeze.y3CakwY4geORIUUCmCm1ZOdKe/Yud27HBkAGOl9Y6'),
(52, 'roxana.petrescu', '$2b$12$JZV0XlVkpmEo7falSF3NcOJKcjEGDOaJgQz4/POWMrG3C4WWVlZi6'),
(53, 'adriana.popa', '$2b$12$TN4uCb2g/5zaRNSAmorO8.F3Q4nPIWsN1.N457BPJrciGeOZX.wf.'),
(54, 'gabriel.ionescu', '$2b$12$w5C7OMjzPkIEHvXBHzPel.uUiOwnHFFfTESyPkIk2AVWnOxDE5qYm'),
(55, 'mihaela.dinu', '$2b$12$ZRJCFwH2oT7S/Sq8a1UnxOWrAhSwczolOofKY2JBUyG0.UTTlQX5S'),
(56, 'radu.florescu', '$2b$12$HQPSO0pUQXFuwy4R4KeVi.0Rr.vAtvEQZv3Wa5rt4vkX01N9taPYW'),
(57, 'andreea.muresan', '$2b$12$LBpwoXcY1tcd234zieFh/Oah8/D6teEl1sIaX6B7nb03maQIhBm2q'),
(58, 'claudiu.pavel', '$2b$12$T5tIuCynjJzNXKZnIPl9vOrsixcCYIM/l6jKiqXcohncgnfIXZGbK'),
(59, 'elena.stoica', '$2b$12$ZOOvE8q5N0Y0pRSjWAlc0eiIlVz8n8UlP1ymV/94FAeIdHzj9kLeu'),
(60, 'dan.marinescu', '$2b$12$6QODnLj2V0E.67tioqgmg.HEENbR7K8D26Ba/1u2MDaBB2sRnr6xG'),
(80, 'trf.mitzaaa', '$2b$12$jP0TRtT6XrKQsP7thsniJed/7xouVtZsdziAW7.GGUPmEo7kHseDC'),
(82, 'bianca.ionescu', '$2b$12$oZjtVgrAoTltCWzjBzXv6.o7dFRknbN0scn7YnMC28UgKUWGpc116'),
(83, 'darius.lupse', '$2b$12$ezS6/mDz2.ZYJ1HhRvrA8ug.egnCg7Qde.jthbQ4WT2LXDVrdn1Ki'),
(84, 'darius.nistor', '$2b$12$YMCBcQUIwzcsfNnueSWYi.h/LJScSAsKJa2dQdHWZuFJs3wChu6my'),
(85, 'ioana.dumitrescu', '$2b$12$4dQSzU2AVrrQLzO7.z28feNQI6N6fVQoK83Yla1WMDPrO93zZQadC'),
(86, 'luca.marinescu', '$2b$12$3Hvi0WORJWik.FAf/O4XVeSbj5vYj16ZwnIox8FpVN5TIccO39ZFy'),
(87, 'maria.lungu', '$2b$12$B7/m9444P78gd.r6UuQAkuMOMq.EaPpkQKZYaDBfqnOy1nq7WJ5pC'),
(88, 'mihai.georgescu', '$2b$12$xyhzYVSH15zQVamt9swP0uTaYCeUkIy8D5htfEezW9HXhidWUhqKa'),
(89, 'teodora.enache', '$2b$12$cCtnbTBV2uPjw2WcfeeLu.AoG3WcoBRbOlisK5U5SqnGYmGeezrz.'),
(90, 'vlad.radu', '$2b$12$hdUKXA3ldCPA6VqR93Rhxur2A0oqW6FmvPqpruAKZ95ZBGYwSPTVW');

-- --------------------------------------------------------

--
-- Table structure for table `user_roles`
--

CREATE TABLE `user_roles` (
  `user_id` int NOT NULL,
  `role` enum('admin','student','teacher','head_teacher') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `user_roles`
--

INSERT INTO `user_roles` (`user_id`, `role`) VALUES
(1, 'admin'),
(43, 'teacher'),
(44, 'student'),
(45, 'student'),
(46, 'student'),
(47, 'student'),
(48, 'student'),
(49, 'student'),
(50, 'student'),
(51, 'student'),
(52, 'student'),
(53, 'teacher'),
(53, 'head_teacher'),
(54, 'teacher'),
(54, 'head_teacher'),
(55, 'teacher'),
(56, 'teacher'),
(57, 'teacher'),
(58, 'teacher'),
(59, 'teacher'),
(60, 'teacher'),
(69, 'student'),
(70, 'student'),
(71, 'student'),
(80, 'student'),
(82, 'student'),
(83, 'student'),
(84, 'student'),
(85, 'student'),
(86, 'student'),
(87, 'student'),
(88, 'student'),
(89, 'student'),
(90, 'student');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `absence_requests`
--
ALTER TABLE `absence_requests`
  ADD PRIMARY KEY (`id`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `class_id` (`class_id`);

--
-- Indexes for table `attendance_current`
--
ALTER TABLE `attendance_current`
  ADD UNIQUE KEY `student_id` (`student_id`);

--
-- Indexes for table `attendance_history`
--
ALTER TABLE `attendance_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `fk_attendance_subject` (`subject_id`);

--
-- Indexes for table `classes`
--
ALTER TABLE `classes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `conduct_grades`
--
ALTER TABLE `conduct_grades`
  ADD PRIMARY KEY (`student_id`);

--
-- Indexes for table `grades`
--
ALTER TABLE `grades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `student_id` (`student_id`);

--
-- Indexes for table `head_teachers`
--
ALTER TABLE `head_teachers`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `students`
--
ALTER TABLE `students`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_class` (`class_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `subjects`
--
ALTER TABLE `subjects`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`);

--
-- Indexes for table `teachers`
--
ALTER TABLE `teachers`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `teacher_assignments`
--
ALTER TABLE `teacher_assignments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `teacher_id` (`teacher_id`),
  ADD KEY `class_id` (`class_id`),
  ADD KEY `subject_id` (`subject_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `user_roles`
--
ALTER TABLE `user_roles`
  ADD PRIMARY KEY (`user_id`,`role`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `absence_requests`
--
ALTER TABLE `absence_requests`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `attendance_history`
--
ALTER TABLE `attendance_history`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `classes`
--
ALTER TABLE `classes`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `grades`
--
ALTER TABLE `grades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=41;

--
-- AUTO_INCREMENT for table `head_teachers`
--
ALTER TABLE `head_teachers`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `students`
--
ALTER TABLE `students`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;

--
-- AUTO_INCREMENT for table `subjects`
--
ALTER TABLE `subjects`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `teachers`
--
ALTER TABLE `teachers`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=61;

--
-- AUTO_INCREMENT for table `teacher_assignments`
--
ALTER TABLE `teacher_assignments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=91;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `absence_requests`
--
ALTER TABLE `absence_requests`
  ADD CONSTRAINT `absence_requests_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `absence_requests_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `attendance_current`
--
ALTER TABLE `attendance_current`
  ADD CONSTRAINT `attendance_current_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`);

--
-- Constraints for table `attendance_history`
--
ALTER TABLE `attendance_history`
  ADD CONSTRAINT `attendance_history_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`),
  ADD CONSTRAINT `fk_attendance_subject` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`);

--
-- Constraints for table `conduct_grades`
--
ALTER TABLE `conduct_grades`
  ADD CONSTRAINT `conduct_grades_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `grades`
--
ALTER TABLE `grades`
  ADD CONSTRAINT `grades_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`id`);

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `students`
--
ALTER TABLE `students`
  ADD CONSTRAINT `fk_class` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`),
  ADD CONSTRAINT `students_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `teacher_assignments`
--
ALTER TABLE `teacher_assignments`
  ADD CONSTRAINT `teacher_assignments_ibfk_1` FOREIGN KEY (`teacher_id`) REFERENCES `teachers` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `teacher_assignments_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `teacher_assignments_ibfk_3` FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`id`);

--
-- Constraints for table `user_roles`
--
ALTER TABLE `user_roles`
  ADD CONSTRAINT `fk_user_roles_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
