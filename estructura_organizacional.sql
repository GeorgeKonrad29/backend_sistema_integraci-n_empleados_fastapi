-- Estructura organizacional completa basada en roles.csv
-- Tabla de JERARQUIA con 56 roles (ID 1 a 56)

INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (1, 'Asamblea de Socios', 'Máximo Órgano', NULL);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (2, 'Gerente General', 'Gerencia General', 1);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (3, 'Gerente Administrativo', 'Gerencia Administración', 2);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (4, 'Coordinador de servicios corporativos', 'Servicios generales', 3);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (5, 'Auxiliar de servicios generales y cafetería', 'Servicios generales', 4);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (6, 'Asistente de compras e inventario', 'Servicios generales', 4);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (7, 'Jefe de Infraestructura y Mantenimiento', 'Mantenimiento', 3);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (8, 'Técnico de Mantenimiento Locativo', 'Mantenimiento', 7);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (9, 'Técnico en Electricidad y Climatización', 'Mantenimiento', 7);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (10, 'Gerente Comercial', 'Gerencia comercial', 2);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (11, 'Coordinador de Ventas y Captación', 'Ventas y Captación', 10);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (12, 'Ejecutivo de Captación y Colocación', 'Ventas y Captación', 11);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (13, 'Asesor de Crédito Externo', 'Ventas y Captación', 11);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (14, 'Jefe de Canales', 'Gestión de canales', 10);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (15, 'Coordinador de Sucursales', 'Gestión de canales', 14);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (16, 'Administrador de Canales Digitales', 'Gestión de canales', 14);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (17, 'Coordinador de Marketing y producto', 'Marketing y producto', 10);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (18, 'Analista de Producto', 'Marketing y producto', 17);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (19, 'Especialista en Comunicación y Marca', 'Marketing y producto', 17);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (20, 'Coordinador de Servicio al cliente', 'Servicio al cliente', 10);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (21, 'Oficial de Experiencia al Asociado', 'Servicio al cliente', 20);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (22, 'Analista de Fidelización y Retención', 'Servicio al cliente', 20);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (23, 'Gerente de riesgos', 'Gerencia de riesgo y crédito', 2);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (24, 'Coordinador de Análisis y crédito', 'Análisis de Crédito', 23);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (25, 'Analista de Crédito Senior', 'Análisis de Crédito', 24);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (26, 'Asistente de Verificación y Garantías', 'Análisis de Crédito', 24);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (27, 'Analista de Microcrédito y Terreno', 'Análisis de Crédito', 24);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (28, 'Coordinador de Riesgo Operativo', 'Riesgo Operativo', 23);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (29, 'Oficial de Cumplimiento (SARLAFT)', 'Riesgo Operativo', 28);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (30, 'Analista de Riesgo Operacional', 'Riesgo Operativo', 28);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (31, 'Auditor de Procesos Crediticios', 'Riesgo Operativo', 28);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (32, 'Gerente Financiero', 'Gerencia financiera', 2);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (33, 'Coordinador de Tesorería', 'Tesorería', 32);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (34, 'Analista de Tesorería y Pagos', 'Tesorería', 33);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (35, 'Coordinador de Contabilidad', 'Contabilidad', 32);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (36, 'Analista de Impuestos y Costos', 'Contabilidad', 35);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (37, 'Asistente Contable', 'Contabilidad', 35);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (38, 'Coordinador de Planeación', 'Planeación', 32);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (39, 'Analista de Estudios Económicos', 'Planeación', 38);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (40, 'Gerente de TI', 'Gerencia TI', 2);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (41, 'Coordinador de Infraestructura y Redes', 'Infraestructura y Redes', 40);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (42, 'Administrador de Servidores y Nube', 'Infraestructura y Redes', 41);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (43, 'Coordinador de Desarrollo de Software', 'Desarrollo de Software', 40);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (44, 'Desarrollador Full Stack', 'Desarrollo de Software', 43);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (45, 'Analista de QA', 'Desarrollo de Software', 43);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (46, 'Coordinador de Soporte Técnico', 'Soporte Técnico', 40);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (47, 'Técnico de Soporte Nivel 1', 'Soporte Técnico', 46);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (48, 'Gerente Talento Humano', 'Gerencia de talento humano', 2);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (49, 'Coordinador de Selección y Reclutamiento', 'Selección y Reclutamiento', 48);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (50, 'Analista de Atracción de Talento', 'Selección y Reclutamiento', 49);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (51, 'Coordinador de Formación y Capacitación', 'Formación y Capacitación', 48);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (52, 'Facilitador de Aprendizaje Interno', 'Formación y Capacitación', 51);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (53, 'Coordinador de Nómina y Compensación', 'Nómina', 48);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (54, 'Analista de Prestaciones y Seguridad Social', 'Nómina', 53);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (55, 'Coordinador de Clima Organizacional', 'Clima Organizacional', 48);
INSERT INTO JERARQUIA (id, nombre_cargo, area, id_jefe_inmediato) VALUES (56, 'Especialista en Bienestar y Cultura', 'Clima Organizacional', 55);



INSERT INTO USUARIO (nombre, correo, contrasena, rol, cargo, estado_onboarding) 
VALUES (
    'Gerente General', 
    'gerente@sinergia.com', 
    'pbkdf2_sha256$390000$6b444e44d68c9b408d0b7073ae2d8a4b$xLT9Ki9dhGf/dLJJpJd07aeOiMCB5nr86VRG3uNOx04=',
    'Root', 
    2, 
    'Finalizado'
);


INSERT INTO USUARIO (nombre, correo, contrasena, rol, cargo, estado_onboarding) 
VALUES (
    'Gerente RRHH', 
    'rrhh@sinergia.com', 
    'pbkdf2_sha256$390000$6b444e44d68c9b408d0b7073ae2d8a4b$xLT9Ki9dhGf/dLJJpJd07aeOiMCB5nr86VRG3uNOx04=', 
    'Administrador', 
    48, 
    'Finalizado'
);


INSERT INTO USUARIO (nombre, correo, contrasena, rol, cargo, estado_onboarding) 
VALUES (
    'Jefe Seleccion', 
    'seleccion@sinergia.com', 
    'pbkdf2_sha256$390000$6b444e44d68c9b408d0b7073ae2d8a4b$xLT9Ki9dhGf/dLJJpJd07aeOiMCB5nr86VRG3uNOx04=',
    'Encargado de Area', 
    49, 
    'Finalizado'
);