-- Último registro de cada embarcación hasta @ahora (hora de Perú).
-- Las fechas salen como texto ISO sin zona horaria para que nadie las convierta por error.
WITH ult AS (
    SELECT a.*, ROW_NUMBER() OVER (PARTITION BY a.Embarcacion ORDER BY a.FechaRegistro DESC) AS rn
    FROM ml.ActividadEmbarcacion a
    WHERE a.FechaRegistro <= TRY_CAST(@ahora AS datetime2)
)
SELECT
    Embarcacion,
    CONVERT(varchar(19), FechaRegistro, 126) AS FechaRegistro,
    Latitud, Longitud, Velocidad, Rpm, GalH, PuertoCercano, DistPuertoKm,
    Actividad, Probabilidad, P_entrada_cala, TipoEtiqueta, VersionModelo,
    DATEDIFF(minute, FechaRegistro, TRY_CAST(@ahora AS datetime2)) AS MinDesdeUltimo
FROM ult
WHERE rn = 1
ORDER BY Embarcacion;
