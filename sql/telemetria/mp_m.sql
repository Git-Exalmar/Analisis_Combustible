SELECT 
    CAST(codigo AS varchar(50)) AS id,
    ep, 
    fecha_Registro AS fecha, 
    TRY_CAST(latitud  AS float) * 100000.0 / 60000.0 AS Latitud,   -- la vista divide entre 1e5 en vez de 6e4
    TRY_CAST(longitud AS float) * 100000.0 / 60000.0 AS Longitud,
    TRY_CAST(velocidad AS float) / 10.0 AS Velocidad, 
    TRY_CAST(rumbo AS int) AS Rumbo,
    TRY_CAST(gal_h AS float) / 10.0 AS gal_h, 
    TRY_CAST(rpm AS float) AS rpm 
    FROM 
        dbo.VW_MP_M_ORDENADO 
    WHERE 
        rpm <> '0' AND gal_h <> '0';