USE green_campus_db;

-- Roles
INSERT INTO roles (name, description) VALUES
('admin',    'System administrator with full access'),
('staff',    'Campus staff member'),
('student',  'Regular student'),
('manager',  'Environmental manager');

-- Campus Zones - ENREDD Batna
INSERT INTO zones (name, description, color_code, lat_center, lng_center) VALUES
('Main Building',          'Administrative and main academic building',  '#2196F3', 35.5641, 6.1842),
('Laboratory Complex',     'Science and engineering laboratories',       '#FF9800', 35.5638, 6.1848),
('Library',                'Central library and study areas',            '#9C27B0', 35.5644, 6.1839),
('Green Spaces & Gardens', 'Campus gardens, trees and outdoor areas',   '#4CAF50', 35.5635, 6.1845),
('Parking Area',           'Student and staff parking lots',             '#607D8B', 35.5630, 6.1850),
('Sports Facilities',      'Sports courts and recreational areas',       '#F44336', 35.5628, 6.1840),
('Cafeteria & Canteen',    'Food service and dining area',               '#795548', 35.5642, 6.1855),
('Renewable Energy Units', 'Solar panels and wind turbine installations','#FFEB3B', 35.5633, 6.1835),
('Waste Management Area',  'Waste collection and recycling station',     '#FF5722', 35.5626, 6.1852),
('Student Residence',      'On-campus student housing',                  '#00BCD4', 35.5648, 6.1860);

-- Categories
INSERT INTO categories (name, name_ar, name_fr, description, icon, color) VALUES
('Water Leak',          'تسرب المياه',      'Fuite d\'eau',           'Water leaks, pipe bursts, flooding',         'fa-tint',          '#2196F3'),
('Energy Waste',        'هدر الطاقة',       'Gaspillage d\'énergie',  'Unnecessary lights, AC issues, power waste', 'fa-bolt',          '#FF9800'),
('Waste Management',    'إدارة النفايات',   'Gestion des déchets',    'Overflowing bins, littering, illegal dumps', 'fa-trash',         '#795548'),
('Air Pollution',       'تلوث الهواء',      'Pollution de l\'air',    'Smoke, bad odors, chemical emissions',       'fa-wind',          '#9E9E9E'),
('Green Space Damage',  'تلف المساحات الخضراء','Dégâts espaces verts','Damaged trees, dry plants, soil erosion',   'fa-leaf',          '#4CAF50'),
('Water Pollution',     'تلوث المياه',      'Pollution de l\'eau',    'Contaminated water, sewage problems',        'fa-water',         '#03A9F4'),
('Noise Pollution',     'التلوث الضوضائي',  'Pollution sonore',       'Excessive noise affecting environment',      'fa-volume-up',     '#FF5722'),
('Chemical Hazard',     'خطر كيميائي',      'Risque chimique',        'Dangerous chemical spills or storage',       'fa-skull-crossbones','#F44336'),
('Infrastructure',      'البنية التحتية',   'Infrastructure',          'Broken facilities affecting environment',    'fa-tools',         '#607D8B'),
('Other',               'أخرى',             'Autre',                  'Other environmental concerns',               'fa-exclamation',   '#9E9E9E');

-- Admin user (password: Admin@2024)
INSERT INTO users (username, email, password_hash, full_name, role_id, department) VALUES
('admin',     'admin@enredd.dz',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMN9a8LJFmRmRjxUFqDt.iKWuC',
 'System Administrator',  1, 'IT Department'),
('dr_mansouri','mansouri@enredd.dz','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMN9a8LJFmRmRjxUFqDt.iKWuC',
 'Dr. Ahmed Mansouri',    4, 'Environmental Management'),
('staff_ali', 'ali.staff@enredd.dz','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMN9a8LJFmRmRjxUFqDt.iKWuC',
 'Ali Benali',            2, 'Maintenance'),
('student1',  'student1@enredd.dz', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMN9a8LJFmRmRjxUFqDt.iKWuC',
 'Fatima Zahra Boudiaf',  3, 'Renewable Energy Engineering'),
('student2',  'student2@enredd.dz', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMN9a8LJFmRmRjxUFqDt.iKWuC',
 'Youcef Kerboua',        3, 'Environmental Science');

-- Sample Alerts
INSERT INTO alerts
(title, description, category_id, zone_id, user_id, latitude, longitude, location_name, status, priority, severity_score)
VALUES
('Water pipe leaking near lab entrance',
 'There is a significant water leak from a pipe near laboratory B2 entrance. Water is pooling on the floor creating a slip hazard.',
 1, 2, 4, 35.5638, 6.1848, 'Laboratory Block B - Entrance', 'in_progress', 'high', 8),

('Lights left on all night in Library',
 'The reading room lights in the library section 2 remain on throughout the night even when no one is present. This wastes significant electricity.',
 2, 3, 5, 35.5644, 6.1839, 'Central Library - Reading Room 2', 'validated', 'medium', 5),

('Overflowing waste bins in cafeteria',
 'The main waste bins near the cafeteria exit have been overflowing for 3 days. Waste is spreading on the ground causing hygiene issues.',
 3, 7, 4, 35.5642, 6.1855, 'Cafeteria - Main Exit', 'reported', 'high', 7),

('Dead trees in campus garden',
 'Several trees in the east garden appear to be dead or severely damaged. They may fall and pose a safety risk.',
 5, 4, 5, 35.5635, 6.1845, 'East Campus Garden', 'reported', 'medium', 6),

('Solar panel surface covered with dust',
 'The solar panels installed near the renewable energy units are heavily covered with dust, significantly reducing their energy output.',
 2, 8, 4, 35.5633, 6.1835, 'Solar Panel Installation Area', 'resolved', 'low', 4),

('Chemical smell from lab waste area',
 'Strong chemical odor detected near the waste management area behind labs. Possible improper disposal of lab chemicals.',
 8, 9, 5, 35.5626, 6.1852, 'Lab Waste Storage Area', 'validated', 'critical', 9),

('Broken drainage causing water stagnation',
 'The drainage system in the parking area is blocked, causing large puddles of stagnant water that attract mosquitoes.',
 6, 5, 4, 35.5630, 6.1850, 'Main Parking Lot', 'in_progress', 'high', 7);