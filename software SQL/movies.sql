SELECT name
FROM people
JOIN stars ON stars.person_id = people.id
JOIN movies ON stars.movie_id = movies.id
WHERE movies.year = 2004
ORDER BY people.birth;

/*
-- Display actors names
SELECT name
FROM people
WHERE id IN (

    SELECT person_id
    FROM stars
    WHERE movie_id IN (
        SELECT id 
        FROM movies
        WHERE title = 'Toy Story'
    )
);
/*
SELECT movies.title, ratings.rating
FROM movies
JOIN ratings ON movie.id = rating.movie_id
WHERE movies.year = 21010
ORDER BY ratings.rating DESC,
    movies.title ASC;

/*
SELECT AVG(rating)
FROM ratings
JOIN movies on rating.movie_id = movies.id 
WHERE movies.year = 2012

/*
SELECT title, year
FROM movies 
WHERE title LIKE 'Harry Pottter%'
ORDER BY year ASC;

/*
SELECT COUNT(rating)
FROM ratings
WHERE rating = 10.0;

/*
SELECT title 
FROM movies
WHERE year >= 2018
ORDER BY TITLE ASC;

/*
SELECT birth
FROM people
WHERE name = 'Emma Stone'

/*
-- all movies in 2008
SELECT title
FROM movies
WHERE year = 2008;
