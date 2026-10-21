SET NOCOUNT ON; 
SELECT 
    m.id, 
    e.Embarcacion AS ep, 
    m.fecha, 
    TRY_CAST(m.Latitude  AS float) / 60000.0 AS Latitud,   -- origen: milésimas de minuto
    TRY_CAST(m.Longitude AS float) / 60000.0 AS Longitud,
    TRY_CAST(m.Speed AS float) / 10.0 AS Velocidad, 
    TRY_CAST(m.header AS int) AS Rumbo, 
    TRY_CAST(m.parameter12 AS float) / 3.785 AS gal_h, -- factor de conversión
    TRY_CAST(m.parameter02 AS float) AS rpm 
    FROM [BD_TEL_FLOTA_PRD].[dbo].[MP_E_H] m
    INNER JOIN [BD_TEL_FLOTA_PRD].[dbo].[Embarcacion] e ON m.IdEmbarcacion = e.IdEmbarcacion
    WHERE 
        m.parameter02 <> '0' AND m.parameter12 <> '0';





