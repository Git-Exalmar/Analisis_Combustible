-- Última ejecución del proceso de scoring (el SSE la usa para saber si hay datos nuevos).
SELECT TOP 1
    IdProceso,
    CONVERT(varchar(19), Inicio, 126) AS Inicio,
    CONVERT(varchar(19), Fin, 126) AS Fin,
    CONVERT(varchar(19), UltimoRegistro, 126) AS UltimoRegistro,
    MinDesdeUltimo, RegistrosEscritos, VersionModelo, Estado
FROM ml.ProcesoScoring
ORDER BY IdProceso DESC;
