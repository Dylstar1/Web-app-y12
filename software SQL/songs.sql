SELECT name 
FROM songs
WHERE name LIKE '%feat.%';

-- drake average energy
/*
SELECT AVG(energy) 
FROM songs
JOIN artists ON songs.artists_id = artists.id
WHERE artists.name = 'Drake';

/*
SELECT songs.name 
FROM songs
JOIN artists ON songs.artist_id = artist.id
WHERE artist.name = 'Post Malone';

---SELECT name, tempo
---FROM songs
---ORDER BY tempo DESC; 