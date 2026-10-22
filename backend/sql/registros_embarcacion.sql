-- Serie completa de una embarcación en un rango (mapa y línea de tiempo).
SELECT
    CONVERT(varchar(19), FechaRegistro, 126) AS FechaRegistro,
    Latitud, Longitud, Velocidad, Rpm, GalH, PuertoCercano, DistPuertoKm,
    Actividad, Probabilidad,
    P_ida, P_busqueda, P_entrada_cala, P_cala, P_salida_cala, P_retorno, P_espera, P_puerto
FROM ml.ActividadEmbarcacion
WHERE Embarcacion = @ep
  AND FechaRegistro >= TRY_CAST(@desde AS datetime2)
  AND FechaRegistro <  TRY_CAST(@hasta AS datetime2)
ORDER BY FechaRegistro;
