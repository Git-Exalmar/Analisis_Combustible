SET NOCOUNT ON; 
SELECT 
    m.id, 
    e.Embarcacion AS ep, 
    m.fecha, 
    TRY_CAST(m.Latitude AS float) AS Latitud, 
    TRY_CAST(m.Longitude AS float) AS Longitud, 
    TRY_CAST(m.Speed AS float) / 10.0 AS Velocidad, 
    m.heading AS Rumbo, 
    TRY_CAST(m.GAL_H AS float) / 10.0 AS gal_h, 
    TRY_CAST(m.RPM AS float) AS rpm 
FROM 
    [dbo].[MP_M_H] m 
INNER JOIN 
    [dbo].[Embarcacion] e ON m.IdEmbarcacion = e.IdEmbarcacion 
WHERE 
    m.RPM <> '0' AND m.GAL_H <> '0';