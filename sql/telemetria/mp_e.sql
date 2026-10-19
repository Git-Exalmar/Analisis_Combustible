SELECT 
    [codigo] AS id, 
    [ep], 
    [fecha_registro] AS fecha, 
    TRY_CAST([latitud] AS float) AS Latitud, 
    TRY_CAST([longitud] AS float) AS Longitud, 
    TRY_CAST([velocidad] AS float) AS Velocidad, 
    TRY_CAST([rumbo] AS int) AS Rumbo, 
    TRY_CAST([consumo_gal_h] AS float) AS gal_h, 
    TRY_CAST([rpm] AS float) AS rpm 
    FROM 
        [dbo].[VW_MP_E_ORDENADO] 
    WHERE 
        [rpm] <> '0' AND [consumo_gal_h] <> '0';