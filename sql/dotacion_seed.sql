-- POBLADO DE TABLA DOTACION
-- Este archivo contiene inserciones de muestra para la tabla DOTACION
-- Los encargados corresponden a los nombre_cargo de la tabla JERARQUIA

-- ============================================================================
-- AREA DE DOTACION: Solicitud de uniformes y elementos de protección personal
-- ============================================================================

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Dotación', 'Uniforme corporativo - Talla M, pantalón azul marino');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Dotación', 'Casco de seguridad industrial - Color amarillo, certificado ANSI');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Dotación', 'Guantes de nitrilo - Caja de 100 unidades, talla grande');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Dotación', 'Chaleco reflectante - Neon, talla universal');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Dotación', 'Botas de seguridad - Punta de acero, talla 42');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Dotación', 'Gafas de protección - Protección UV y impacto');

-- ============================================================================
-- AREA DE TECNOLOGIA: Solicitud de credenciales de acceso y hardware
-- ============================================================================

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Laptop Lenovo ThinkBook 15 - 16GB RAM, SSD 512GB');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Monitor Dell UltraSharp 27" - Resolución 2560x1440, USB-C');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Credenciales VPN - Acceso remoto a red corporativa');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Llave de acceso física - Tarjeta magnética, edificio principal');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Mouse y teclado inalámbrico - Equipo Logitech MK850');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Headset Bluetooth profesional - Cancelación de ruido activa');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Jefe de Infraestructura y Mantenimiento', 'Tecnología', 'Carnet de acceso digital - Acceso a sistemas corporativos');

-- ============================================================================
-- AREA DE SERVICIOS GENERALES: Asignación de puesto físico y carnetización
-- ============================================================================

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Servicios Generales', 'Puesto de trabajo - Planta 2, Sector A, Escritorio 45');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Servicios Generales', 'Carnet corporativo - Foto 4x4, acceso multiárea');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Servicios Generales', 'Puesto de trabajo - Planta 3, Sector B, Escritorio 78');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Servicios Generales', 'Parqueadero - Espacio P-45, puerta principal');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Servicios Generales', 'Llave de oficina - Oficina 301, ala administrativa');

-- ============================================================================
-- AREA DE FORMACION Y CAPACITACION: Inducción, plan de formación
-- ============================================================================

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', 'Inducción corporativa - Sesión online, día 1 del onboarding');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', 'Plan de formación nivel I - Trainees, 4 módulos');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', 'Capacitación en Microsoft Office - Excel nivel avanzado, 8 horas');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', 'Certificación ISO - Normas corporativas y cumplimiento');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', 'Taller de competencias blandas - Comunicación efectiva, 6 horas');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', 'Acceso plataforma e-learning - Usuario premium, 1 año');

-- ============================================================================
-- CURSOS: importados desde cursos.txt
-- ============================================================================

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '1. Inducción a la Cultura Cooperativa - Conocer la historia, valores y principios del modelo solidario. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '2. Portafolio de Productos y Servicios - Dominar las características de los ahorros y créditos vigentes. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '3. Prevención de Lavado de Activos (SARLAFT) - Detectar operaciones sospechosas y cumplir con la ley financiera. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '4. Seguridad y Salud en el Trabajo (SST) - Identificar riesgos laborales y protocolos de emergencia. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '5. Brigadas de Primeros Auxilios - Capacitar al personal en respuesta ante accidentes físicos. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '6. Prevención de Acoso Laboral - Fomentar un ambiente de respeto y convivencia sana. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '7. Manejo de Extintores y Evacuación - Actuar correctamente ante incendios o desastres naturales. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '8. Venta Consultiva Financiera - Desarrollar técnicas para ofrecer créditos según la necesidad del socio. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '9. Técnicas de Negociación y Cierre - Mejorar la efectividad en la colocación de servicios financieros. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '10. Captación de Depósitos y Ahorro - Aprender estrategias para atraer liquidez a la cooperativa. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '11. Análisis de Capacidad de Pago - Estudiar la relación ingreso/gasto del solicitante. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '12. Interpretación de Centrales de Riesgo - Aprender a leer e interpretar reportes de burós de crédito. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '13. Evaluación de Garantías Reales - Conocer los aspectos legales de hipotecas y prendas vehiculares. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '14. Gestión de Riesgo Operativo - Identificar fallas en procesos que puedan generar pérdidas. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '15. Gestión de Cobranza Preventiva - Aprender a contactar al socio antes de que caiga en mora. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '16. Actualización en Normas NIIF - Aplicar los estándares internacionales de contabilidad vigentes. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '17. Manejo de Flujo de Caja y Liquidez - Optimizar el dinero disponible para desembolsos diarios. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '18. Preparación de Reportes a Entes de Control - Cumplir con los informes para la Superintendencia. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '19. Ciberseguridad para No Técnicos - Enseñar a evitar phishing y proteger contraseñas. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '20. Manejo del Core Financiero (Software) - Capacitar en el uso de la plataforma principal de la entidad. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '21. Protección de Datos Personales - Cumplir con la ley de Habeas Data y privacidad del socio. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '22. Liderazgo y Trabajo en Equipo - Desarrollar habilidades blandas para coordinadores y jefes. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '23. Inteligencia Emocional en el Trabajo - Brindar herramientas para el manejo del estrés y la empatía. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '24. Comunicación Asertiva - Mejorar el flujo de información interna y externa. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '25. Excel Avanzado para Finanzas - Dominar tablas dinámicas y fórmulas para análisis de datos. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '26. Protocolo de Servicio al Cliente - Estandarizar el saludo y la atención en las sucursales. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '27. Manejo de Clientes Difíciles - Aprender técnicas de desescalamiento de conflictos. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '28. Gestión de PQRS Eficiente - Reducir tiempos de respuesta a reclamos de socios. - Modalidad: Virtual');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '29. Manipulación de Productos Químicos (Para Servicios Generales) - Uso seguro de implementos de aseo. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '30. Mantenimiento Preventivo de Sedes (Para Mantenimiento) - Protocolos de revisión técnica locativa. - Modalidad: Presencial');

INSERT INTO DOTACION (encargado, tipo, especificacion)
VALUES ('Coordinador de Formación y Capacitación', 'Formación y Capacitación', '31. Gestión de Compras y Proveedores - Aprender procesos de licitación y selección de compras. - Modalidad: Virtual');

-- ============================================================================
-- AREA DE BIENES Y SERVICIOS: Inmobiliario e insumos
-- ============================================================================

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Escritorio modular - 160x80cm, color gris, con 3 cajones');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Silla ergonómica - Ajuste de altura, brazos regulables, color negro');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Estantería de oficina - 5 estantes, capacidad 100kg por nivel');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Papelería inicial - 10 resmas papel, 6 bolígrafos, 3 libretas');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Lámpara LED de escritorio - 40W, temperatura ajustable');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Organizador de escritorio - Compartimentos múltiples, acero inoxidable');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Dispensador de agua fría/caliente - Para sala de descanso');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Cafetera para oficina - 12 tazas, automática');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Extintor tipo ABC - 5 kg, para área de trabajo');

INSERT INTO DOTACION (encargado, tipo, especificacion) 
VALUES ('Coordinador de servicios corporativos', 'Bienes y Servicios', 'Botiquín de primeros auxilios - Completo, para emergencias');
