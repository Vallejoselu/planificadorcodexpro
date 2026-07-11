-- Datos ficticios para pruebas manuales. No se cargan automaticamente.
-- Usar solo sobre una base de datos de prueba o una copia.

INSERT INTO repartidores(
    nombre,
    horas,
    zona,
    doble_turno,
    puede_hasta_la_una,
    prioridad_comida,
    prioridad_noche,
    prioridad_grela,
    observaciones
) VALUES
('Demo Ana', 10, 'Ronda', 1, 1, 70, 50, 30, 'Dato de demostracion'),
('Demo Luis', 20, 'Ronda', 1, 1, 50, 80, 30, 'Dato de demostracion'),
('Demo Marta', 30, 'Grela', 1, 1, 50, 50, 90, 'Dato de demostracion');

INSERT INTO descansos(repartidor_id, dia_inicio, dia_fin)
SELECT id, 'lunes', 'martes'
FROM repartidores
WHERE nombre='Demo Ana';

INSERT INTO descansos(repartidor_id, dia_inicio, dia_fin)
SELECT id, 'martes', 'miercoles'
FROM repartidores
WHERE nombre='Demo Luis';

INSERT INTO descansos(repartidor_id, dia_inicio, dia_fin)
SELECT id, 'jueves', 'viernes'
FROM repartidores
WHERE nombre='Demo Marta';

INSERT INTO restaurantes(
    nombre,
    direccion,
    zona,
    telefono,
    prioridad,
    activo,
    horario_comida,
    horario_cena,
    observaciones
) VALUES
('Demo Ronda Centro', 'Calle Demo 1', 'Ronda', '600000001', 80, 1, '13:00-16:00', '20:00-23:30', 'Dato de demostracion'),
('Demo Grela Norte', 'Poligono Demo 2', 'Grela', '600000002', 60, 1, '13:00-16:00', '20:00-23:30', 'Dato de demostracion');

INSERT INTO turnos(tipo, nombre, hora_inicio, hora_fin, color, duracion, activo)
VALUES
('Comida', 'Demo Comida', '13:00', '16:00', '#2563EB', 3, 1),
('Cena', 'Demo Cena', '20:00', '23:30', '#16A34A', 3.5, 1);
