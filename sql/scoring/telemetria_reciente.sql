-- Telemetría reciente de las dos fuentes vigentes (mp_e y mp_m).
-- Mismas transformaciones que sql/telemetria/mp_e.sql y mp_m.sql.
-- El parámetro ? (dos veces) es la fecha desde la que se lee, en hora de Perú.
SELECT
    CAST(codigo AS varchar(50)) AS id,
    ep,
    fecha_registro AS fecha,
    TRY_CAST(latitud AS float)   AS Latitud,
    TRY_CAST(longitud AS float)  AS Longitud,
    TRY_CAST(velocidad AS float) AS Velocidad,
    TRY_CAST(rumbo AS int)       AS Rumbo,
    TRY_CAST(consumo_gal_h AS float) AS gal_h,
    TRY_CAST(rpm AS float)       AS rpm,
    'mp_e' AS origen
FROM [BD_TEL_FLOTA_PRD].[dbo].[VW_MP_E_ORDENADO]
WHERE rpm <> '0' AND consumo_gal_h <> '0'
  AND TRY_CAST(fecha_registro AS datetime2) >= ?

UNION ALL

SELECT
    CAST(codigo AS varchar(50)) AS id,
    ep,
    fecha_Registro AS fecha,
    TRY_CAST(latitud AS float)  * 100000.0 / 60000.0 AS Latitud,
    TRY_CAST(longitud AS float) * 100000.0 / 60000.0 AS Longitud,
    TRY_CAST(velocidad AS float) / 10.0 AS Velocidad,
    TRY_CAST(rumbo AS int)              AS Rumbo,
    TRY_CAST(gal_h AS float) / 10.0     AS gal_h,
    TRY_CAST(rpm AS float)              AS rpm,
    'mp_m' AS origen
FROM [BD_TEL_FLOTA_PRD].[dbo].[VW_MP_M_ORDENADO]
WHERE rpm <> '0' AND gal_h <> '0'
  AND TRY_CAST(fecha_Registro AS datetime2) >= ?;