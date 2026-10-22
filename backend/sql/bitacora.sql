-- Registros de todas las embarcaciones en un rango, para armar la bitácora (segmentos).
SELECT
    Embarcacion,
    CONVERT(varchar(19), FechaRegistro, 126) AS FechaRegistro,
    Actividad, Probabilidad, Velocidad
FROM ml.ActividadEmbarcacion
WHERE FechaRegistro >= TRY_CAST(@desde AS datetime2)
  AND FechaRegistro <  TRY_CAST(@hasta AS datetime2)
ORDER BY Embarcacion, FechaRegistro;
