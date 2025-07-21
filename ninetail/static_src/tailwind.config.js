/** @type {import('tailwindcss').Config} */
module.exports = {
               content: [
                 './templates/**/*.{html,js}',
                 './static/**/*.{js,html}',
                 './**/*.html',
               ],
               theme: {
                extend: {
                  keyframes: { // keyframes começa e termina aqui
                    'rotate': {
                      '0%': {
                        transform: 'translate(-50%, -50%) rotate(0deg)'
                      },
                      '100%': {
                        transform: 'translate(-50%, -50%) rotate(1turn)'
                      },
                    },
                  },
                  animation: { // 'animation' agora está no mesmo nível de 'keyframes'
                    'rotate': 'rotate 4s linear infinite',
                  },
                },
              },
              plugins: [],
            }
          