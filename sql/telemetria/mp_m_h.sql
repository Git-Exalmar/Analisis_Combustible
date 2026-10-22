SET NOCOUNT ON; 
SELECT 
    CAST(m.id AS varchar(50)) AS id, 
    e.Embarcacion AS ep, 
    m.fecha, 
    TRY_CAST(m.Latitude  AS float) / 60000.0 AS Latitud,   -- origen: milésimas de minuto
    TRY_CAST(m.Longitude AS float) / 60000.0 AS Longitud,
    TRY_CAST(m.Speed AS float) / 10.0 AS Velocidad, 
    TRY_CAST(m.heading AS int) AS Rumbo, 
    TRY_CAST(m.GAL_H AS float) / 10.0 AS gal_h, 
    TRY_CAST(m.RPM AS float) AS rpm 
FROM 
    [dbo].[MP_M_H] m 
INNER JOIN 
    [dbo].[Embarcacion] e ON m.IdEmbarcacion = e.IdEmbarcacion 
WHERE 
    m.RPM <> '0' AND m.GAL_H <> '0';