 WITH FaenasBase AS (
        SELECT p.[IND_IdEmbarcacion], p.[idTemporadaRegion], p.[GalonesConsumo], p.[FechaHoraZarpe], p.[FechaHoraArriboReal],
               e.[Embarcacion], e.[CB], e.[Casco], e.[RSW], t.[temporada],
               (DATEDIFF(minute, p.[FechaHoraZarpe], p.[FechaHoraArriboReal]) * 1.0 / 60) AS DuracionFaenaHoras
        FROM [DB_Indicadores].[app].[View_PescaDescargas] p
        LEFT JOIN [dbo].[Embarcacion] e ON p.[IND_IdEmbarcacion] = e.[IdEmbarcacion]
        LEFT JOIN [dbo].[TemporadaRegion] tr ON p.[IdTemporadaRegion] = tr.[idtemporadaregion]
        LEFT JOIN [dbo].[Temporada] t ON tr.[idtemporada] = t.[idtemporada]
        WHERE p.[idTemporadaRegion] >= 57
    )

    SELECT * FROM FaenasBase
    WHERE GalonesConsumo > 0 AND DuracionFaenaHoras > 0 AND DuracionFaenaHoras <= 120
    AND  Embarcacion NOT IN ('ZHENNA 3', 'PONTEVEDRA', 'MARIA MERCEDES 5668', 'CORINTIA');