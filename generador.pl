% Reglas para determinar la altura de un punto según ruido 
altura(X, Y, Altura) :-
    Perlin is sin(X / 10) * cos(Y / 10),  
    BaseAltura is Perlin * 10,
    (BaseAltura > 0 -> Altura is BaseAltura; Altura is 0),
    (X > -1, X < 1 -> Altura is 0; true).  % Río en el centro

% Colores basados en la altura
color(Altura, R, G, B) :-
    (Altura < 1 -> R = 139, G = 69, B = 19;      % Río (marrón)
    Altura < 3 -> R = 34, G = 139, B = 34;    % Hierba
    R = 0, G = 0, B = 255).                % Montañas (azul)