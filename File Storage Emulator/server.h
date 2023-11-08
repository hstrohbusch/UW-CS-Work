#include "message.h"

void intHandler(int dummy);
void serLookup(message_t *m);
void serStat(message_t *m);
void serWrite(message_t *m);
void serRead(message_t *m);
void serCreat(message_t *m);
void serUnlink(message_t *m);
void serShutdown(message_t *m);
unsigned int get_bit(unsigned int *bitmap, int position);
void set_bit(unsigned int *bitmap, int position);