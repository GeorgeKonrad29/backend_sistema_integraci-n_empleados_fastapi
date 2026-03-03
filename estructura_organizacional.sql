-- 1. INSERCIÓN DE CARGOS DE ALTA GERENCIA (Reportan al Gerente General o Asamblea)
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (1, 'Gerente General', 'Gerencia General', NULL);
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (2, 'Gerente Administrativo', 'Gerencia Administracion', 1);
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (3, 'Gerente Comercial', 'Gerencia Comercial', 1);
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (4, 'Gerente de Riesgo y Crédito', 'Gerencia Riesgo y Crédito', 1);
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (5, 'Gerente de Finanzas', 'Gerencia Finanzas', 1);
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (6, 'Gerente de TI', 'Gerencia TI', 1);
INSERT INTO CARGOS (id, nombre_cargo, area, id_jefe_inmediato) VALUES (7, 'Gerente de Talento Humano', 'Gerencia Talento Humano', 1);

-- 2. GERENCIA DE ADMINISTRACIÓN
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Coordinador de Servicios Corporativos', 'Servicios Generales', 2);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Auxiliar de Mantenimiento', 'Mantenimiento', 8); -- Reporta al Coordinador

-- 3. GERENCIA COMERCIAL
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Ventas', 'Ventas y Captación', 3);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Asesor Comercial', 'Ventas y Captación', 10);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Coordinador de Canales Digitales', 'Gestión de Canales', 3);

-- 4. GERENCIA DE RIESGO Y CRÉDITO
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Análisis de Crédito', 'Análisis de crédito', 4);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista de Crédito Senior', 'Análisis de crédito', 13);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Oficial de Riesgo Operativo', 'Riesgo Operativo', 4);

-- 5. GERENCIA DE FINANZAS
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Coordinador de Tesorería', 'Tesorería', 5);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista de Tesorería', 'Tesorería', 16);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Contador General', 'Contabilidad', 5);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Auxiliar Contable', 'Contabilidad', 18);

-- 6. GERENCIA DE TI
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Infraestructura', 'Infraestructura y redes', 6);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Ingeniero de Soporte', 'Soporte', 20);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Líder de Desarrollo', 'Desarrollo', 6);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista Programador', 'Desarrollo', 22);

-- 7. GERENCIA DE TALENTO HUMANO
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Jefe de Selección', 'Selección y reclutamiento', 7);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Especialista de Formación', 'Formación y capacitación', 7);
INSERT INTO CARGOS (nombre_cargo, area, id_jefe_inmediato) VALUES ('Analista de Nómina', 'Nómina', 7);