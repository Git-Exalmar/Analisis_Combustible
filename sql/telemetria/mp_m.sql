SELECT 
    codigo AS id,
    ep, 
    fecha_Registro AS fecha, 
    TRY_CAST(latitud AS float) AS Latitud, 
    TRY_CAST(longitud AS float) AS Longitud, 
    TRY_CAST(velocidad AS float) / 10.0 AS Velocidad, 
    rumbo AS Rumbo, TRY_CAST(gal_h AS float) / 10.0 AS gal_h, 
    TRY_CAST(rpm AS float) AS rpm 
    FROM 
        dbo.VW_MP_M_ORDENADO 
    WHERE 
        rpm <> '0' AND gal_h <> '0';